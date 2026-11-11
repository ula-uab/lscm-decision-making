"""Lot sizing at the plants (lot_sizing.md): the weekly plan of each plant, which
checks whether the plant can assemble, week by week and model by model, what the
master plan of M4 (retailers.md) gives it each month. M4 is called, not copied:
it is solved with the orders that the retailers place each month. Written with
PuLP and solved with HiGHS; and what the notebook lot_sizing.ipynb shows.

The computations, each with its data as arguments:

1. ``weekly_orders`` and ``monthly_orders``: the orders of each retailer, by
   model and week, and by month (Table 4);
2. ``master_plan``: M4 with those orders (Table 7);
3. ``seasonal_split``, ``shipment_mix``, ``least_stock`` and
   ``weekly_shipments``: what each plant ships each week and the least stock it
   holds at the end of each month (Tables 7 to 9);
4. ``weekly_plan``: one plan for each month, one after the other, each in the
   two stages of step 6 (Tables 10 to 12);
5. ``limit_case``: the two limit cases of step 7, with the plans expected
   without solving the model, ``lot_for_lot`` and ``one_lot_a_month``;
6. ``line_hours``: assembly, setups, capacity overload and spare capacity by
   month (Table 13);
7. ``run``: the plans of the six months with the data of part d) (Tables 14
   and 18).

Quantities are exact: fractions, not floating point, so that every rounding,
half up, starts from the exact value.

The notebook calls one function per step: ``show_orders``, ``show_master_plan``,
``show_shipments``, ``show_weekly_plan``, ``show_limit_case``,
``show_line_hours`` and ``show_runs``.
"""

from __future__ import annotations

import functools
import math
from fractions import Fraction

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from . import figures, retailers
from .data import (ARCS_M4, ASSEMBLY_TIME, AVERAGE_ORDERS, BACKORDER_SHARE, CENTRAL, CREW_COST, FIRST_BIKE_CHECK,
                   HOLIDAYS, HOURS_PER_DAY, LOCAL, MODELS, MONTH_DAYS, NODES, NODES_M4, PLACES_M4, PLANT_STOCK_0,
                   PRODUCT_MIX, RAIL_TERMINAL, REGIONAL, RETAILERS, SEASONAL_INDEX, SETUP_TIME, VALUE_FACTOR,
                   WEEK_FACTOR, WEEKS, F, K, K_h, K_h_node_m4, K_n, T, c_b, c_h, c_h_node_m4, c_l)
from .model import _optimal
from .show import COLOURS, SHORT, _display, _light, _number

WEEKDAYS = 5                       # Monday to Friday
WEEK_SHARE = Fraction(12, 52)      # the share of a month that a week is
PLANTS = F


def exact(x) -> Fraction:
    """A datum written as a decimal number, as an exact fraction: 0,867 is 867/1000."""
    return x if isinstance(x, Fraction) else Fraction(str(x))


def half_up(x, decimals: int = 0) -> Fraction:
    """x rounded half up to ``decimals`` decimals, from its exact value."""
    scale = 10 ** decimals
    return Fraction(math.floor(exact(x) * scale + Fraction(1, 2)), scale)


def _cumulative(values) -> list[int]:
    """Whole numbers whose sums from the first add up to the sums of ``values``
    rounded half up: each value is the difference between two consecutive
    rounded sums."""
    out, total, before = [], Fraction(0), 0
    for v in values:
        total += v
        now = int(half_up(total))
        out.append(now - before)
        before = now
    return out


def _largest_remainder(total: int, share: dict) -> dict:
    """``total`` split in whole numbers in proportion to ``share``, keeping the
    total: each part is rounded down, and what is left over goes to the parts
    with the largest remainders."""
    raw = {j: total * share[j] for j in share}
    out = {j: math.floor(raw[j]) for j in share}
    for j in sorted(share, key=lambda j: raw[j] - out[j], reverse=True)[:total - sum(out.values())]:
        out[j] += 1
    return out


# ---------------------------------------------------------------------------
# Calendar (§1, Tables 1 to 3)
# ---------------------------------------------------------------------------

def _month_of(day: int) -> str:
    """The month of a day of the horizon, counted from 0 on 1 January."""
    for t in T:
        if day < MONTH_DAYS[t]:
            return t
        day -= MONTH_DAYS[t]
    raise ValueError("The day is after the end of June.")


def _day(month: str, day: int) -> int:
    return sum(MONTH_DAYS[t] for t in T[:T.index(month)]) + day - 1


def week_months(week: int) -> list[str]:
    """The month of each day from Monday to Friday of a week."""
    return [_month_of(7 * (week - 1) + k) for k in range(WEEKDAYS)]


def days_in_month(week: int, month: str) -> int:
    """n_wt: the days from Monday to Friday of week w in month t."""
    return week_months(week).count(month)


def weekdays_of_month(month: str) -> int:
    """N_t: the days from Monday to Friday of month t."""
    return sum(days_in_month(w, month) for w in WEEKS)


def plan_weeks() -> dict:
    """The weeks of the plan of each month: those with most of their days from
    Monday to Friday in it. The last one is the week of the end of the month."""
    weeks = {t: [] for t in T}
    for w in WEEKS:
        months = week_months(w)
        weeks[max(T, key=months.count)].append(w)
    return weeks


def working_days(plant: str, holidays: dict = HOLIDAYS) -> dict:
    """The working days of each week at a plant: Monday to Friday, less its
    holidays."""
    off = {_day(t, d) for t, d in holidays[plant]}
    return {w: sum(1 for k in range(WEEKDAYS) if 7 * (w - 1) + k not in off) for w in WEEKS}


def available_capacity(plant: str, holidays: dict = HOLIDAYS) -> dict:
    """K_w: the available capacity of the line of a plant in each week (h), its
    working days times one shift."""
    return {w: HOURS_PER_DAY * days for w, days in working_days(plant, holidays).items()}


# ---------------------------------------------------------------------------
# 1. Orders (§1, Table 4)
# ---------------------------------------------------------------------------

def _week_index(model: str, week: int, seasonal: dict) -> Fraction:
    """The seasonal index of a model in a week: the average of the indices of the
    months of its days from Monday to Friday."""
    return sum(exact(seasonal[model][t]) for t in week_months(week)) / WEEKDAYS


def weekly_orders(average: dict = AVERAGE_ORDERS, mix: dict = PRODUCT_MIX, seasonal: dict = SEASONAL_INDEX,
                  factor: dict = WEEK_FACTOR) -> dict:
    """The orders of each retailer for each model in each week (whole bikes), by
    (r, j, w): its average orders a month, times the share of the model, times the
    seasonal index of the week, times 12/52, times the factor of the week. The
    orders accumulated from week 1 are rounded half up."""
    out = {}
    for r in average:
        for j in MODELS:
            raw = [average[r] * exact(mix[r][j]) * _week_index(j, w, seasonal) * WEEK_SHARE * exact(factor[w])
                   for w in WEEKS]
            out.update({(r, j, w): q for w, q in zip(WEEKS, _cumulative(raw))})
    return out


def model_orders(weekly: dict) -> dict:
    """The orders of each retailer for each model in each month (bikes, not
    rounded), by (r, j, t): a week that falls in two months gives each month the
    share of its orders of its days in it."""
    retailers_ = sorted({r for r, _, _ in weekly}, key=RETAILERS.index)
    return {(r, j, t): sum(Fraction(days_in_month(w, t), WEEKDAYS) * weekly[r, j, w] for w in WEEKS)
            for r in retailers_ for j in MODELS for t in T}


def monthly_orders(weekly: dict) -> dict:
    """The orders of each retailer in each month, the four models together (whole
    bikes), by (r, t): Table 4. The orders accumulated from January are rounded
    half up."""
    by_model = model_orders(weekly)
    retailers_ = sorted({r for r, _, _ in by_model}, key=RETAILERS.index)
    out = {}
    for r in retailers_:
        raw = [sum(by_model[r, j, t] for j in MODELS) for t in T]
        out.update({(r, t): q for t, q in zip(T, _cumulative(raw))})
    return out


# ---------------------------------------------------------------------------
# 2. Master plan: M4 with the orders of Table 4 (§2, Table 7)
# ---------------------------------------------------------------------------

def _value(x: float) -> Fraction:
    """A value of the solver of M4 as a fraction, to the thousandth of a bike."""
    return Fraction(round(x * 1000), 1000)


def master_plan(order: dict) -> dict | None:
    """M4 solved with the orders of each retailer in each month, by (r, t). Returns
    its cost (EUR), the orders and, by month, the bikes that each plant assembles, ships to the
    network and holds at the end of the month, the stock of the network (plants and
    warehouses), and the deliveries and backorders of each retailer. None if M4 has
    no solution."""
    solution = retailers.solve(order={k: float(v) for k, v in order.items()})
    if solution is None:
        return None
    shipped = {(f, t): sum(_value(solution["flow"][a, t]) for a, arc in enumerate(ARCS_M4) if arc["origin"] == f)
               for f in PLANTS for t in T}
    return {
        "cost": solution["cost"], "orders": dict(order),
        "assembled": {(f, t): _value(solution["assembly"][f, t]) for f in PLANTS for t in T},
        "shipped": shipped,
        "stock": {(f, t): _value(solution["stock"][f, t]) for f in PLANTS for t in T},
        "network stock": {t: sum(_value(solution["stock"][i, t]) for i in NODES) for t in T},
        "deliveries": {k: _value(v) for k, v in solution["deliveries"].items()},
        "backorders": {k: _value(v) for k, v in solution["backorders"].items()},
        "lost sales": {k: _value(v) for k, v in solution["lost sales"].items()},
    }


# ---------------------------------------------------------------------------
# 3. Shipments and least stock of each plant (§2, Tables 7 to 9)
# ---------------------------------------------------------------------------

def _share(values: dict) -> dict:
    total = sum(values.values())
    return {j: Fraction(values[j]) / total for j in values}


def seasonal_split(network_stock: dict, by_model: dict, final: dict = PLANT_STOCK_0) -> dict:
    """The share of each model in the seasonal stock at the end of each month: the
    orders of each model, all retailers together, in the months in which that
    stock is used, the first group of later consecutive months in which the stock
    of the network falls. Stock that does not fall in any later month is split with
    the models of the required final stock."""
    out = {}
    for k, t in enumerate(T):
        used = []
        for s in range(k + 1, len(T)):
            if network_stock[T[s]] < network_stock[T[s - 1]]:
                used.append(T[s])
            elif used:
                break
        if used:
            out[t] = _share({j: sum(by_model[r, j, s] for r in RETAILERS for s in used) for j in MODELS})
        else:
            out[t] = _share({j: sum(final[f][j] for f in final) for j in MODELS})
    return out


def _delivered_mix(master: dict, by_model: dict) -> dict:
    """The bikes of each model that the retailers receive in each month: the
    deliveries of a retailer serve first its backorders and then its orders of the
    month, and each bike keeps the product mix of the orders of the month in which
    it was ordered."""
    out = {(j, t): Fraction(0) for j in MODELS for t in T}
    for r in RETAILERS:
        pending = []                                   # [bikes, month ordered], oldest first
        for t in T:
            ordered = master["orders"][r, t]
            lost = master["lost sales"][r, t]
            pending.append([ordered, t])
            left = master["deliveries"][r, t]
            for item in pending:
                served = min(item[0], left)
                mix = _share({j: by_model[r, j, item[1]] for j in MODELS})
                for j in MODELS:
                    out[j, t] += served * mix[j]
                item[0] -= served
                left -= served
            for item in pending:                          # lost sales leave the oldest orders first
                gone = min(item[0], lost)
                item[0] -= gone
                lost -= gone
            pending = [item for item in pending if item[0] > 0]
    return out


def shipment_mix(master: dict, by_model: dict, split: dict) -> dict:
    """The product mix of the shipments of the plants in each month (Table 8):
    what the retailers receive plus the change in the stock of the warehouses,
    split among the models as the seasonal stock."""
    delivered = _delivered_mix(master, by_model)
    warehouses = {t: master["network stock"][t] - sum(master["stock"][f, t] for f in PLANTS) for t in T}
    out = {}
    for k, t in enumerate(T):
        before = {j: 0 for j in MODELS} if k == 0 else {j: warehouses[T[k - 1]] * split[T[k - 1]][j] for j in MODELS}
        out[t] = _share({j: delivered[j, t] + warehouses[t] * split[t][j] - before[j] for j in MODELS})
    return out


def least_stock(master: dict, split: dict, final: dict = PLANT_STOCK_0) -> dict:
    """h_min: the least stock of each model at each plant at the end of each month
    (whole bikes), by (f, t): the stock of M4 at the plant, split as the seasonal
    stock keeping its total; at the end of June, the required final stock."""
    return {(f, t): dict(final[f]) if t == T[-1] else _largest_remainder(int(master["stock"][f, t]), split[t])
            for f in PLANTS for t in T}


def weekly_shipments(master: dict, mix: dict) -> dict:
    """x_fjw: the bikes of each model that each plant ships to the network in each
    week (whole bikes), by (f, j, w), Table 9. The shipments of a month are spread
    evenly over its days from Monday to Friday, and the shipments accumulated from
    week 1 are rounded half up."""
    out = {}
    for f in PLANTS:
        for j in MODELS:
            raw = [sum(Fraction(days_in_month(w, t), weekdays_of_month(t)) * master["shipped"][f, t] * mix[t][j]
                       for t in T) for w in WEEKS]
            out.update({(f, j, w): q for w, q in zip(WEEKS, _cumulative(raw))})
    return out


def six_month_mix(weekly: dict) -> dict:
    """The product mix of the orders of the six months, all retailers together."""
    return _share({j: sum(q for (_, i, _), q in weekly.items() if i == j) for j in MODELS})


def same_mix(shipments: dict, least: dict, mix: dict, final: dict = PLANT_STOCK_0) -> tuple[dict, dict]:
    """The shipments and the least stock of part d) with the same product mix in
    every week: the bikes that each plant ships in a week (Table 9) split among the
    models with ``mix``, the shipments accumulated from week 1 rounded half up; and
    the least stock at the end of each month split with ``mix``, except at the end
    of June, the required final stock."""
    x = {}
    for f in PLANTS:
        for j in MODELS:
            raw = [sum(shipments[f, i, w] for i in MODELS) * mix[j] for w in WEEKS]
            x.update({(f, j, w): q for w, q in zip(WEEKS, _cumulative(raw))})
    h_min = {(f, t): dict(final[f]) if t == T[-1] else _largest_remainder(sum(least[f, t].values()), mix)
             for f in PLANTS for t in T}
    return x, h_min


@functools.lru_cache(maxsize=1)
def _base() -> dict:
    """Everything that the weekly plans take from the master plan, with the data of
    §1: computed once."""
    weekly = weekly_orders()
    order = monthly_orders(weekly)
    master = master_plan(order)
    by_model = model_orders(weekly)
    split = seasonal_split(master["network stock"], by_model)
    mix = shipment_mix(master, by_model, split)
    return {"weekly orders": weekly, "orders": order, "model orders": by_model, "master": master,
            "split": split, "mix": mix, "shipments": weekly_shipments(master, mix),
            "least stock": least_stock(master, split), "six-month mix": six_month_mix(weekly)}


def base() -> dict:
    """The orders, the master plan, the product mixes, the shipments and the least
    stock with the data of §1 (a copy, which can be changed)."""
    return dict(_base())


# ---------------------------------------------------------------------------
# 4. The weekly lot plan of a plant (§3, steps 4 to 6)
# ---------------------------------------------------------------------------

def holding_cost(plant: str, holding: dict = c_h, factor: dict = VALUE_FACTOR) -> dict:
    """c^h_j: the holding cost of each model at a plant (EUR/(bike·week)): its
    holding cost of M4 times 12/52 times the factor of the model, rounded to the
    cent."""
    return {j: half_up(holding[plant] * WEEK_SHARE * exact(factor[j]), 2) for j in MODELS}


def setup_cost(setup_time: dict) -> dict:
    """c^set_j: the setup cost of each model (EUR/setup), from its setup time."""
    return {j: CREW_COST * exact(setup_time[j]) + FIRST_BIKE_CHECK for j in MODELS}


def _solver():
    """HiGHS, solving each model to its exact optimum: no relative or absolute gap."""
    return pulp.HiGHS(msg=False, gapRel=0, gapAbs=0)


def build_month(weeks: list, shipments: dict, least: dict, initial: dict, assembly: dict, setup: dict,
                setup_costs: dict, holding: dict, storage: int, capacity: dict):
    """The model of the plan of one month at one plant, not solved, with the
    objective of stage 1. Returns the model and its variables ("p", "h", "delta" by
    (j, w); "o" by w)."""
    model = pulp.LpProblem("lot_sizing", pulp.LpMinimize)
    # p = bikes assembled (integer); h = stock at the end of the week (integer); delta = 1 if
    # the model is set up and assembled in the week; o = capacity overload (h)
    p = {(j, w): model.add_variable(f"p_{j}_{w}", lowBound=0, cat="Integer") for j in MODELS for w in weeks}
    h = {(j, w): model.add_variable(f"h_{j}_{w}", lowBound=0, cat="Integer") for j in MODELS for w in weeks}
    delta = {(j, w): model.add_variable(f"delta_{j}_{w}", lowBound=0, upBound=1, cat="Integer")
             for j in MODELS for w in weeks}
    o = {w: model.add_variable(f"o_{w}", lowBound=0) for w in weeks}
    for j in MODELS:
        for k, w in enumerate(weeks):
            before = initial[j] if k == 0 else h[j, weeks[k - 1]]
            # Balance between periods
            model += (before + p[j, w] == shipments[j, w] + h[j, w], f"balance_{j}_{w}")
            # Only if: a model is assembled only in a week in which it is set up
            model += (p[j, w] <= (shipments[j, w] + storage) * delta[j, w], f"setup_{j}_{w}")
        # Least stock at the end of the month
        model += (h[j, weeks[-1]] >= least[j], f"least_stock_{j}")
    for w in weeks:
        # Capacity of the line, relaxed by the capacity overload
        model += (pulp.lpSum(float(assembly[j]) * p[j, w] + float(setup[j]) * delta[j, w] for j in MODELS)
                  <= capacity[w] + o[w], f"capacity_{w}")
        # Storage capacity
        model += (pulp.lpSum(h[j, w] for j in MODELS) <= storage, f"storage_{w}")
    model += pulp.lpSum(o.values())
    return model, {"p": p, "h": h, "delta": delta, "o": o}


def _stage_2_cost(var: dict, setup_costs: dict, holding: dict):
    return pulp.lpSum(float(setup_costs[j]) * var["delta"][j, w] + float(holding[j]) * var["h"][j, w]
                      for j, w in var["p"])


def _other_plan(model, var: dict, plan: dict, cost: float) -> bool:
    """True if another plan with the same capacity overload and the same setup and
    holding cost assembles different bikes: the model looks for the plan with the
    same costs that differs most from ``plan``. The model is changed."""
    model += (_stage_2_cost(var["model"], var["setup costs"], var["holding"]) <= cost + 1e-6, "least_cost")
    gap = []
    for (j, w), p in var["model"]["p"].items():
        bound = var["bound"][j, w]
        z = model.add_variable(f"z_{j}_{w}", lowBound=0, upBound=1, cat="Integer")
        g = model.add_variable(f"g_{j}_{w}", lowBound=0)
        model += (g <= p - plan[j, w] + bound * (1 - z), f"gap_up_{j}_{w}")
        model += (g <= plan[j, w] - p + bound * z, f"gap_down_{j}_{w}")
        gap.append(g)
    model.sense = pulp.LpMaximize
    model.setObjective(pulp.lpSum(gap))
    if not _optimal(model.solve(_solver())):
        return False
    return pulp.value(model.objective) > 0.5


def month_plan(weeks: list, shipments: dict, least: dict, initial: dict, assembly: dict, setup: dict,
               holding: dict, storage: int, capacity: dict, check: bool = False) -> dict | None:
    """The plan of one month at one plant, in the two stages of step 6: the least
    capacity overload, and among the plans with it, the least setup and holding
    cost. Returns the bikes assembled and the setups by (j, w), and, with
    ``check``, whether another plan has the same costs. None if it has no plan."""
    setup_costs = setup_cost(setup)
    model, var = build_month(weeks, shipments, least, initial, assembly, setup, setup_costs, holding, storage,
                             capacity)
    if not _optimal(model.solve(_solver())):
        return None
    overload = pulp.value(model.objective)
    model += (pulp.lpSum(var["o"].values()) <= overload + 1e-6, "least_overload")
    model.setObjective(_stage_2_cost(var, setup_costs, holding))
    if not _optimal(model.solve(_solver())):
        return None
    plan = {k: round(v.value()) for k, v in var["p"].items()}
    out = {"assembled": plan, "setups": {k: round(v.value()) for k, v in var["delta"].items()}}
    if check:
        bound = {(j, w): shipments[j, w] + storage for j in MODELS for w in weeks}
        out["other plan"] = _other_plan(model, {"model": var, "setup costs": setup_costs, "holding": holding,
                                                "bound": bound}, plan, pulp.value(model.objective))
    return out


def _week(row_stock: dict, assembled: dict, setups: dict, assembly: dict, setup: dict, capacity: float) -> dict:
    hours = sum(exact(assembly[j]) * assembled[j] for j in MODELS)
    setup_hours = sum(exact(setup[j]) * setups[j] for j in MODELS)
    used = hours + setup_hours
    return {"available": Fraction(capacity), "assembled": assembled, "stock": row_stock, "setups": setups,
            "assembly hours": hours, "setup hours": setup_hours,
            "overload": max(Fraction(0), used - capacity), "spare": max(Fraction(0), capacity - used)}


def _cost(weeks: dict, setup: dict, holding: dict) -> Fraction:
    setup_costs = setup_cost(setup)
    return sum(setup_costs[j] * row["setups"][j] + holding[j] * row["stock"][j]
               for row in weeks.values() for j in MODELS)


def _plant_data(plant: str, assembly, setup, holding, storage, capacity, initial) -> tuple:
    return (assembly or ASSEMBLY_TIME[plant], setup or SETUP_TIME[plant], holding or holding_cost(plant),
            K_h[plant] if storage is None else storage, capacity or available_capacity(plant),
            initial or PLANT_STOCK_0[plant])


def weekly_plan(plant: str, shipments: dict | None = None, least: dict | None = None, assembly: dict | None = None,
                setup: dict | None = None, holding: dict | None = None, storage: int | None = None,
                capacity: dict | None = None, initial: dict | None = None, check: bool = False) -> dict | None:
    """The weekly lot plan of a plant for the six months: one plan for each month,
    with the weeks of that month, each starting with the stock that the previous
    one left. Data not given are those of §1: ``shipments`` by (f, j, w), ``least``
    by (f, t), ``assembly`` and ``setup`` times and ``holding`` cost by model,
    ``storage`` capacity, available ``capacity`` by week and ``initial`` stock by
    model. Returns, for each week, the available capacity, the bikes assembled and
    in stock at the end of the week, the setups, the hours of assembly and of
    setups, the capacity overload and the spare capacity; the setup and holding
    cost (EUR); with ``check``, the months in which another plan has the same
    costs; and the least stock and the storage capacity of the plan. Returns None,
    with the month, if a month has no plan."""
    data = _base()
    shipments = data["shipments"] if shipments is None else shipments
    least = data["least stock"] if least is None else least
    assembly, setup, holding, storage, capacity, stock = _plant_data(plant, assembly, setup, holding, storage,
                                                                     capacity, initial)
    stock = dict(stock)
    weeks, others = {}, []
    for t, plan_weeks_ in plan_weeks().items():
        x = {(j, w): shipments[plant, j, w] for j in MODELS for w in plan_weeks_}
        plan = month_plan(plan_weeks_, x, least[plant, t], stock, assembly, setup, holding, storage, capacity, check)
        if plan is None:
            return {"no plan": t}
        if plan.get("other plan"):
            others.append(t)
        for w in plan_weeks_:
            assembled = {j: plan["assembled"][j, w] for j in MODELS}
            stock = {j: stock[j] + assembled[j] - x[j, w] for j in MODELS}
            weeks[w] = _week(stock, assembled, {j: plan["setups"][j, w] for j in MODELS}, assembly, setup,
                             capacity[w])
    return {"plant": plant, "weeks": weeks, "cost": _cost(weeks, setup, holding),
            "other plans": others if check else None, "least": {t: least[plant, t] for t in T}, "storage": storage}


# ---------------------------------------------------------------------------
# 5. Validation of step 7: two limit cases with a known plan
# ---------------------------------------------------------------------------

LIMIT_CASES = ["A · expensive holding", "B · expensive setups"]
LIMIT_CAPACITY = 1000     # h of available capacity in every week: the line never binds
LIMIT_HOLDING = 10000     # EUR/(bike·week), case A
LIMIT_SETUP_TIME = 100    # h/setup, case B
NO_STORAGE_LIMIT = 10000  # bikes, case B


def _known_plan(plant: str, lots, shipments: dict | None, least: dict | None, assembly: dict | None,
                setup: dict | None, holding: dict | None, capacity: dict | None, initial: dict | None) -> dict:
    """A plan built by a rule, evaluated in the model: ``lots(weeks, x, least, stock)``
    gives the bikes of each model assembled in each week of a month."""
    data = _base()
    shipments = data["shipments"] if shipments is None else shipments
    least = data["least stock"] if least is None else least
    assembly, setup, holding, _, capacity, stock = _plant_data(plant, assembly, setup, holding, 0, capacity, initial)
    stock = dict(stock)
    weeks = {}
    for t, plan_weeks_ in plan_weeks().items():
        x = {(j, w): shipments[plant, j, w] for j in MODELS for w in plan_weeks_}
        lot = lots(plan_weeks_, x, least[plant, t], stock)
        for w in plan_weeks_:
            assembled = {j: lot.get((j, w), 0) for j in MODELS}
            stock = {j: stock[j] + assembled[j] - x[j, w] for j in MODELS}
            weeks[w] = _week(stock, assembled, {j: int(assembled[j] > 0) for j in MODELS}, assembly, setup,
                             capacity[w])
    return {"plant": plant, "weeks": weeks, "cost": _cost(weeks, setup, holding), "other plans": None,
            "least": {t: least[plant, t] for t in T}, "storage": K_h[plant]}


def lot_for_lot(plant: str, shipments: dict | None = None, least: dict | None = None, assembly: dict | None = None,
                setup: dict | None = None, holding: dict | None = None, capacity: dict | None = None,
                initial: dict | None = None) -> dict:
    """The expected plan of limit case A: each week assembles, model by model, what
    it ships less the stock it holds; in the week of the end of the month it also
    assembles what it lacks of the least stock. Returns what ``weekly_plan``
    returns, evaluated in the model."""
    def lots(weeks, x, least, stock):
        out, stock = {}, dict(stock)
        for w in weeks:
            for j in MODELS:
                out[j, w] = max(0, x[j, w] + (least[j] if w == weeks[-1] else 0) - stock[j])
                stock[j] += out[j, w] - x[j, w]
        return out
    return _known_plan(plant, lots, shipments, least, assembly, setup, holding, capacity, initial)


def one_lot_a_month(plant: str, shipments: dict | None = None, least: dict | None = None,
                    assembly: dict | None = None, setup: dict | None = None, holding: dict | None = None,
                    capacity: dict | None = None, initial: dict | None = None) -> dict:
    """The expected plan of limit case B: one lot of each model in each month, in
    the first week whose shipments the stock does not cover, with what the month
    still needs of that model, its least stock included; if the stock covers the
    shipments but not the least stock, in the week of the end of the month."""
    def lots(weeks, x, least, stock):
        out = {}
        for j in MODELS:
            need = sum(x[j, w] for w in weeks) + least[j] - stock[j]
            if need <= 0:
                continue
            shipped = 0
            for w in weeks:
                shipped += x[j, w]
                if shipped > stock[j] or w == weeks[-1]:
                    out[j, w] = need
                    break
        return out
    return _known_plan(plant, lots, shipments, least, assembly, setup, holding, capacity, initial)


def limit_case(plant: str, case: str) -> dict:
    """A limit case of step 7 at a plant, one of ``LIMIT_CASES``: the plan of the
    model with its data ("model") and the plan expected without solving it
    ("expected"), and the weeks in which their lots differ ("different weeks")."""
    capacity = {w: LIMIT_CAPACITY for w in WEEKS}
    if case == LIMIT_CASES[0]:
        holding = {j: LIMIT_HOLDING for j in MODELS}
        model = weekly_plan(plant, holding=holding, capacity=capacity)
        expected = lot_for_lot(plant, holding=holding, capacity=capacity)
    elif case == LIMIT_CASES[1]:
        setup = {j: LIMIT_SETUP_TIME for j in MODELS}
        model = weekly_plan(plant, setup=setup, capacity=capacity, storage=NO_STORAGE_LIMIT)
        expected = one_lot_a_month(plant, setup=setup, capacity=capacity)
        model["storage"] = expected["storage"] = None
    else:
        raise ValueError(f"The limit case must be one of {', '.join(LIMIT_CASES)}.")
    different = [w for w in WEEKS if model["weeks"][w]["assembled"] != expected["weeks"][w]["assembled"]]
    return {"model": model, "expected": expected, "different weeks": different}


# ---------------------------------------------------------------------------
# 6. Hours of the line by month (Table 13)
# ---------------------------------------------------------------------------

def line_hours(plan: dict) -> dict:
    """The hours of the line of a plan by month and over the six months, by t and
    "Six months": the weeks, the available capacity, the hours of assembly and of
    setups, the capacity overload and the spare capacity (h), and the capacity
    overload as a share of the available capacity."""
    out = {}
    for t, weeks in {**plan_weeks(), "Six months": WEEKS}.items():
        rows = [plan["weeks"][w] for w in weeks]
        sums = {k: sum((row[k] for row in rows), Fraction(0))
                for k in ("available", "assembly hours", "setup hours", "overload", "spare")}
        sums["weeks"] = f"{weeks[0]}–{weeks[-1]}"
        sums["overload share"] = sums["overload"] / sums["available"]
        out[t] = sums
    return out


# ---------------------------------------------------------------------------
# 7. The runs of part d) (Tables 14 and 15)
# ---------------------------------------------------------------------------

NO_HOLIDAYS = {f: [] for f in PLANTS}
RUNS = ["As planned", "No holidays", "Half the setup times", "Setup times of plant 1",
        "Six-month product mix in every week"]


def run(plant: str, name: str, check: bool = False) -> dict | None:
    """The weekly plan of a plant for the six months with the data of a run of
    part d), one of ``RUNS``. None for the setup times of plant 1 at plant 1."""
    if name == "As planned":
        return weekly_plan(plant, check=check)
    if name == "No holidays":
        return weekly_plan(plant, capacity=available_capacity(plant, NO_HOLIDAYS), check=check)
    if name == "Half the setup times":
        return weekly_plan(plant, setup={j: exact(v) / 2 for j, v in SETUP_TIME[plant].items()}, check=check)
    if name == "Setup times of plant 1":
        return None if plant == PLANTS[0] else weekly_plan(plant, setup=SETUP_TIME[PLANTS[0]], check=check)
    if name == "Six-month product mix in every week":
        data = _base()
        x, h_min = same_mix(data["shipments"], data["least stock"], data["six-month mix"])
        return weekly_plan(plant, shipments=x, least=h_min, check=check)
    raise ValueError(f"The run must be one of {', '.join(RUNS)}.")


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def fixed(x, decimals: int = 2) -> str:
    """A number in European format, rounded half up from its exact value."""
    return _number(float(half_up(x, decimals)), decimals)


def _bikes(values: dict) -> str:
    return "; ".join(_number(values[j]) for j in MODELS)


def _plant(plant: str) -> str:
    if plant not in PLANTS:
        raise ValueError(f"The plant must be one of {', '.join(PLANTS)}.")
    return plant


def _name(node: str) -> str:
    """A node or a retailer with its place: «Retailer 1 (Lleida)»."""
    return f"{node} ({PLACES_M4[node][0]})"


def _retailer(retailer: str) -> str:
    for r in RETAILERS:
        if retailer in (r, _name(r)):
            return r
    raise ValueError(f"The retailer must be one of {', '.join(RETAILERS)}.")


def orders_table(order: dict) -> pd.DataFrame:
    """Table 4: the orders of each retailer in each month."""
    table = pd.DataFrame({_name(r): {t: order[r, t] for t in T} for r in RETAILERS}).T
    table.loc["All"] = table.sum()
    table["Six months"] = table.sum(axis=1)
    return table.rename_axis("Orders (bikes)")


def weekly_orders_table(weekly: dict, retailer: str) -> pd.DataFrame:
    """The orders of one retailer in each week, by model, with the total of each
    week and of the 26 weeks."""
    table = pd.DataFrame({w: {j: weekly[retailer, j, w] for j in MODELS} for w in WEEKS}).T
    table["Total"] = table.sum(axis=1)
    table.loc["26 weeks"] = table.sum()
    return table.rename_axis("Week")


def show_orders(retailer: str = "Retailer 1", show_table: bool = False) -> None:
    """The orders of the retailers: the six-month totals by model, and the orders of
    each retailer in each month and in each week, by model, in two figures or, with
    ``show_table``, in Table 4 and the table of the weekly orders of one retailer."""
    retailer = _retailer(retailer)
    data = _base()
    totals = {j: sum(q for (_, i, _), q in data["weekly orders"].items() if i == j) for j in MODELS}
    print("Orders of the 26 weeks, all retailers (bikes): "
          + "; ".join(f"{j} {_number(totals[j])}" for j in MODELS)
          + "; product mix " + "; ".join(f"{fixed(100 * data['six-month mix'][j], 1)} %" for j in MODELS) + ".")
    if show_table:
        _display(orders_table(data["orders"]))
        print(f"{_name(retailer)}: orders in each week, by model (bikes).")
        _display(weekly_orders_table(data["weekly orders"], retailer))
    else:
        _monthly_orders_figure(data["orders"])
        _orders_figure(data["weekly orders"])


def _monthly_orders_figure(order: dict) -> None:
    """The orders of each month, stacked by retailer, with the orders of each
    retailer inside its part of the bar and the total above it (Table 4)."""
    rows = {_name(r): [order[r, t] for t in T] for r in RETAILERS}
    figures.orders_figure(rows, "Orders of each retailer in each month, the four models together: the data with which "
                          f"M4 is solved ({_number(sum(sum(v) for v in rows.values()))} bikes in the six months)")


@_light
def _orders_figure(weekly: dict) -> None:
    """One panel for each retailer, with the same scale: its orders of each week
    stacked by model."""
    top = max(sum(weekly[r, j, w] for j in MODELS) for r in RETAILERS for w in WEEKS)
    fig, axes = plt.subplots(3, 2, figsize=(12, 8), sharex=True)
    colours = plt.get_cmap("tab10")
    for ax, r in zip(axes.flat, RETAILERS):
        bottom = [0] * len(WEEKS)
        for k, j in enumerate(MODELS):
            values = [weekly[r, j, w] for w in WEEKS]
            ax.bar(WEEKS, values, bottom=bottom, color=colours(k), width=0.75, label=j)
            bottom = [b + v for b, v in zip(bottom, values)]
        for t, weeks in plan_weeks().items():
            ax.axvline(weeks[-1] + 0.5, color="0.6", lw=0.8, ls=":")
            ax.annotate(t, ((weeks[0] + weeks[-1]) / 2, top * 1.04), ha="center", fontsize=8)
        ax.set_ylim(0, top * 1.13)
        ax.set_xticks(WEEKS)
        ax.tick_params(labelsize=7)
        ax.set_title(_name(r), fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("Orders (bikes)")
    for ax in axes[-1]:
        ax.set_xlabel("Week")
    axes[0, 1].legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.suptitle("Orders of each retailer in each week, by model", fontsize=11)
    fig.tight_layout()
    plt.show()


def network_tables() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The data of M4 at the warehouses, on the arcs and at the retailers."""
    warehouses = pd.DataFrame({_name(i): {
        "Holding cost (€/(bike·month))": _number(c_h_node_m4[i]),
        "Storage capacity (bikes)": _number(K_h_node_m4[i]),
        "Node capacity (bikes/month)": _number(K_n[i]) if i in K_n else "—"} for i in [CENTRAL, *REGIONAL, *LOCAL]}).T
    arcs = pd.DataFrame([{"Arc": a + 1, "Origin": _name(arc["origin"]), "Destination": _name(arc["destination"]),
                          "Mode": arc["mode"], "Transport cost (€/bike)": _number(arc["cost"], 2),
                          "Arc capacity (bikes/month)": _number(arc["capacity"])}
                         for a, arc in enumerate(ARCS_M4)]).set_index("Arc")
    retailers_ = pd.DataFrame({_name(r): {"Backorder share": _number(BACKORDER_SHARE[r], 1),
                                          "Lost-sale cost (€/bike)": _number(c_l[r])} for r in RETAILERS}).T
    return (warehouses.rename_axis("Warehouse"), arcs, retailers_.rename_axis("Retailer"))


def master_plan_table(master: dict, least: dict, plant: str) -> pd.DataFrame:
    """Table 7 for one plant: what the plan of M4 sets for it in each month, with the
    least stock of each model at the end of the month."""
    rows = {"Assembly": {t: float(master["assembled"][plant, t]) for t in T},
            "Shipments to the network": {t: float(master["shipped"][plant, t]) for t in T},
            "Stock at the end of the month": {t: float(master["stock"][plant, t]) for t in T},
            **{f"Least stock, {j}": {t: least[plant, t][j] for t in T} for j in MODELS}}
    return pd.DataFrame(rows).T.rename_axis(f"{_name(plant)}, bikes")


@_light
def _master_plan_figure(master: dict, least: dict) -> None:
    """For each plant, above, the bikes it has to assemble and ship to the network in
    each month, with its capacity; below, the stock it has to hold at the end of each
    month, stacked by model: the least stock of each model."""
    fig, axes = plt.subplots(2, len(PLANTS), figsize=(15, 6.6), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]})
    x = range(len(T))
    colours = plt.get_cmap("tab10")
    top = max(K[f][t] for f in PLANTS for t in T) * 1.3
    stock_top = max(float(master["stock"][f, t]) for f in PLANTS for t in T) * 1.2
    for k, f in enumerate(PLANTS):
        above, below = axes[0, k], axes[1, k]
        assembly = [float(master["assembled"][f, t]) for t in T]
        shipments = [float(master["shipped"][f, t]) for t in T]
        above.bar([i - 0.21 for i in x], assembly, 0.41, color=COLOURS[f], label="assembly")
        above.bar([i + 0.21 for i in x], shipments, 0.41, color=COLOURS[f], alpha=0.4, label="shipments to the network")
        above.step([-0.5, *x, len(T) - 0.5], [K[f][T[0]], *(K[f][t] for t in T), K[f][T[-1]]], where="mid",
                   color="black", lw=1, ls="--", label="capacity")
        for i in x:
            for value, dx in ((assembly[i], -0.21), (shipments[i], 0.21)):
                if value:                  # inside the top of the bar, clear of the capacity line
                    above.text(i + dx, value - top * 0.02, _number(value), ha="center", va="top", fontsize=6.5,
                               color="white" if dx < 0 else "black")
        above.set_ylim(0, top)
        above.set_title(_name(f), fontsize=10)
        above.legend(fontsize=7, loc="upper left", frameon=False, ncol=3)
        bottom = [0.0] * len(T)
        for q, j in enumerate(MODELS):
            values = [float(least[f, t][j]) for t in T]
            below.bar(x, values, 0.55, bottom=bottom, color=colours(q), label=j)
            bottom = [b + v for b, v in zip(bottom, values)]
        for i in x:
            below.text(i, bottom[i] + stock_top * 0.02, _number(bottom[i]), ha="center", fontsize=7)
        below.set_ylim(0, stock_top)
        below.set_xticks(list(x), T)
        for ax in (above, below):
            ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].set_ylabel("Bikes per month")
    axes[1, 0].set_ylabel("Stock at the end\nof the month (bikes)")
    axes[1, -1].legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0), title="Least stock", title_fontsize=7)
    fig.suptitle("Master plan M4: what each plant has to assemble, ship to the network and hold at the end of "
                 "each month", fontsize=11)
    fig.tight_layout()
    plt.show()


def show_master_plan(show_tables: bool = False) -> None:
    """The data of M4 on the figure of the network; and M4 solved with the orders of
    Table 4: its cost, the figure of its plan at the plants and the stock of the
    network. With ``show_tables``, the data and the plan in tables (Table 7) instead
    of the figures."""
    print(f"The {RAIL_TERMINAL.lower()} ({PLACES_M4[RAIL_TERMINAL][0]}) holds no stock. Every warehouse starts and "
          "ends the six months with no stock. Node capacity: the bikes that the warehouse can receive in a month. "
          "Backorder share: of the orders that a retailer does not receive in their month, the share that is "
          f"backordered; the rest is lost sales. Backorder cost: {_number(c_b)} €/(bike·month); lost-sale cost: "
          f"{_number(c_l[RETAILERS[0]])} €/bike at every retailer.")
    if show_tables:
        for table in network_tables():
            _display(table)
    else:
        _network_figure()
    data = _base()
    master = data["master"]
    print(f"M4 with the orders of the retailers: cost {_number(master['cost'], 2)} €; backorders "
          f"{_number(float(sum(master['backorders'].values())))} and lost sales "
          f"{_number(float(sum(master['lost sales'].values())))} bikes.")
    if show_tables:
        for f in PLANTS:
            _display(master_plan_table(master, data["least stock"], f))
    else:
        _master_plan_figure(master, data["least stock"])
    print("Stock of the network, plants and warehouses, at the end of each month (bikes): "
          + "; ".join(f"{t} {_number(float(master['network stock'][t]))}" for t in T) + ".")


def _network_figure() -> None:
    """The network of M4 as in the statement, with the data of each node under its
    label and the transport cost and the arc capacity on each arc."""
    figures.network(NODES_M4, range(len(ARCS_M4)), {node: figures.data_text(node) for node in NODES_M4},
                    {a: figures.arc_text(arc) for a, arc in enumerate(ARCS_M4)},
                    "Data of M4. Plants: unit assembly cost · capacity; holding cost · storage capacity. Warehouses: "
                    "holding cost · storage capacity.\nArcs: transport cost (€/bike) · arc capacity (bikes/month); "
                    f"the arcs to the retailers have an arc capacity of {_number(ARCS_M4[-1]['capacity'])} bikes/month.")


def mix_table(mix: dict, split: dict, master: dict) -> pd.DataFrame:
    """Table 8: the product mix of the shipments and the split of the seasonal
    stock, by month (%). A month that ends with no stock has no split."""
    rows = {}
    for j in MODELS:
        rows[f"Shipments, {j}"] = {t: fixed(100 * mix[t][j], 1) for t in T}
    for j in MODELS:
        rows[f"Seasonal stock, {j}"] = {t: fixed(100 * split[t][j], 1) if master["network stock"][t] else "—"
                                        for t in T}
    return pd.DataFrame(rows).T.rename_axis("Product mix (%)")


def shipments_table(shipments: dict, plants=PLANTS) -> pd.DataFrame:
    """Table 9: the shipments of each plant in each week, by model."""
    rows = {w: {f: _bikes({j: shipments[f, j, w] for j in MODELS}) for f in plants} for w in WEEKS}
    rows["Total"] = {f: _bikes({j: sum(shipments[f, j, w] for w in WEEKS) for j in MODELS}) for f in plants}
    return pd.DataFrame(rows).T.rename_axis("Week")


def _mix_tables(mix: dict, split: dict, master: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The product mix of the shipments of each month, and the split of the
    seasonal stock at the end of each month with the stock of the network (Table 8,
    one table for each)."""
    shipments = pd.DataFrame({t: {j: fixed(100 * mix[t][j], 1) for j in MODELS} for t in T})
    stock = pd.DataFrame({t: {j: fixed(100 * split[t][j], 1) if master["network stock"][t] else "—" for j in MODELS}
                          for t in T})
    stock.loc["Stock of the network (bikes)"] = [_number(float(master["network stock"][t])) for t in T]
    return (shipments.rename_axis("Product mix of the shipments (%)"),
            stock.rename_axis("Split of the seasonal stock (%)"))


def _plant_shipments_table(shipments: dict, plant: str) -> pd.DataFrame:
    """The shipments of one plant in each week, one column for each model (its
    column of Table 9)."""
    table = pd.DataFrame({w: {j: shipments[plant, j, w] for j in MODELS} for w in WEEKS}).T
    table["Total"] = table.sum(axis=1)
    table.loc["26 weeks"] = table.sum()
    return table.rename_axis("Week")


def _least_stock_table(least: dict, plant: str) -> pd.DataFrame:
    """The least stock of one plant at the end of each month, one column for each
    model; its total is the stock at the end of the month of the master plan."""
    weeks = plan_weeks()
    table = pd.DataFrame({(t, weeks[t][-1]): {j: least[plant, t][j] for j in MODELS} for t in T}).T
    table["Total"] = table.sum(axis=1)
    return table.rename_axis(["Month", "Required at the end of week"])


def show_shipments(plant: str = "Plant 1", show_tables: bool = False) -> None:
    """The product mix of the shipments and the split of the seasonal stock, and the
    shipments of one plant in each week and its least stock at the end of each
    month, by model: in two figures or, with ``show_tables``, in tables."""
    plant = _plant(plant)
    data = _base()
    if show_tables:
        for table in _mix_tables(data["mix"], data["split"], data["master"]):
            _display(table)
        print(f"{_name(plant)}: shipments to the network in each week (bikes).")
        _display(_plant_shipments_table(data["shipments"], plant))
        print(f"{_name(plant)}: least stock at the end of each month (bikes). Its total is the stock at the end of "
              "the month of the master plan (§2).")
        _display(_least_stock_table(data["least stock"], plant))
    else:
        _mix_figure(data["mix"], data["split"], data["master"])
        _shipments_figure(plant, data["shipments"], data["least stock"])


@_light
def _mix_figure(mix: dict, split: dict, master: dict) -> None:
    """Left: the product mix of the shipments of each month. Right: the split of the
    seasonal stock at the end of each month, with the stock of the network above
    each bar."""
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), sharey=True)
    colours = plt.get_cmap("tab10")
    titles = ("Product mix of the shipments of each month",
              "Split of the seasonal stock at the end of each month\n(above each bar: stock of the network, "
              "plants and warehouses)")
    for ax, shares, title in zip(axes, (mix, split), titles):
        for i, t in enumerate(T):
            if shares is split and not master["network stock"][t]:
                ax.text(i, 50, "no stock", ha="center", va="center", fontsize=8, color="0.4", rotation=90)
                continue
            bottom = 0.0
            for k, j in enumerate(MODELS):
                value = 100 * float(shares[t][j])
                ax.bar(i, value, 0.62, bottom=bottom, color=colours(k), label=j if i == 0 else None)
                ax.text(i, bottom + value / 2, fixed(value, 1), ha="center", va="center", fontsize=7, color="white")
                bottom += value
            if shares is split:
                ax.text(i, 102, f"{_number(float(master['network stock'][t]))} bikes", ha="center", va="bottom",
                        fontsize=8)
        ax.set_xticks(range(len(T)), T)
        ax.set_ylim(0, 112)
        ax.set_title(title, fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Share of each model (%)")
    axes[1].legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    plt.show()


@_light
def _shipments_figure(plant: str, shipments: dict, least: dict) -> None:
    """Above: the shipments of the plant in each week, stacked by model. Below: its
    least stock at the end of each month, stacked by model, in the week in which it
    is required."""
    fig, (above, below) = plt.subplots(2, 1, figsize=(13, 6.2), sharex=True, gridspec_kw={"height_ratios": [1.6, 1]})
    colours = plt.get_cmap("tab10")
    bottom = [0] * len(WEEKS)
    for k, j in enumerate(MODELS):
        values = [shipments[plant, j, w] for w in WEEKS]
        above.bar(WEEKS, values, 0.75, bottom=bottom, color=colours(k), label=j)
        bottom = [b + v for b, v in zip(bottom, values)]
    top = max(max(bottom) * 1.2, 1)
    for w, total in zip(WEEKS, bottom):
        above.text(w, total + top * 0.01, _number(total), ha="center", fontsize=7)
    stock_top = max(max(sum(least[plant, t].values()) for t in T) * 1.25, 10)
    for t, weeks in plan_weeks().items():
        for ax in (above, below):
            ax.axvline(weeks[-1] + 0.5, color="0.6", lw=0.8, ls=":")
        above.text((weeks[0] + weeks[-1]) / 2, top * 0.97, t, ha="center", fontsize=8)
        level = 0
        for k, j in enumerate(MODELS):
            value = least[plant, t][j]
            below.bar(weeks[-1], value, 0.75, bottom=level, color=colours(k))
            if value >= stock_top * 0.07:
                below.text(weeks[-1], level + value / 2, _number(value), ha="center", va="center", fontsize=7,
                           color="white")
            level += value
        below.text(weeks[-1], level + stock_top * 0.02, _number(level), ha="center", fontsize=7)
    above.set_ylim(0, top)
    above.set_ylabel("Shipments (bikes)")
    above.set_title(f"{_name(plant)}: shipments to the network in each week, by model", fontsize=10)
    above.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    below.set_ylim(0, stock_top)
    below.set_ylabel("Least stock (bikes)")
    below.set_title(f"{_name(plant)}: least stock at the end of each month, by model, required at the end of the "
                    "last week of the month; its total is the stock at the end of the month of the master plan",
                    fontsize=9)
    below.set_xticks(WEEKS)
    below.tick_params(labelsize=7)
    below.set_xlabel("Week")
    for ax in (above, below):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    plt.show()


def plan_table(plan: dict) -> pd.DataFrame:
    """Tables 10 to 12: the weekly lot plan of a plant."""
    rows = {}
    for w, row in plan["weeks"].items():
        rows[w] = {"Available capacity (h)": _number(float(row["available"])),
                   "Assembled (bikes)": _bikes(row["assembled"]), "Stock at the end (bikes)": _bikes(row["stock"]),
                   "Assembly (h)": fixed(row["assembly hours"]), "Setups (h)": fixed(row["setup hours"]),
                   "Capacity overload (h)": fixed(row["overload"])}
    weeks = plan["weeks"].values()
    rows["Total"] = {"Available capacity (h)": _number(float(sum(r["available"] for r in weeks))),
                     "Assembled (bikes)": _bikes({j: sum(r["assembled"][j] for r in weeks) for j in MODELS}),
                     "Stock at the end (bikes)": "",
                     "Assembly (h)": fixed(sum(r["assembly hours"] for r in weeks)),
                     "Setups (h)": fixed(sum(r["setup hours"] for r in weeks)),
                     "Capacity overload (h)": fixed(sum(r["overload"] for r in weeks))}
    return pd.DataFrame(rows).T.rename_axis("Week")


def _plan_by_model(plan: dict) -> pd.DataFrame:
    """The weekly lot plan of a plant in one table, one column for each model: the
    form of Tables 10 to 12 for the notebook."""
    rows = {}
    for w, row in plan["weeks"].items():
        rows[w] = {("Available capacity (h)", ""): _number(float(row["available"])),
                   **{("Assembly (bikes)", j): row["assembled"][j] for j in MODELS},
                   **{("Stock at the end of the week (bikes)", j): row["stock"][j] for j in MODELS},
                   ("Assembly (h)", ""): fixed(row["assembly hours"]), ("Setups (h)", ""): fixed(row["setup hours"]),
                   ("Capacity overload (h)", ""): fixed(row["overload"])}
    weeks = plan["weeks"].values()
    rows["Total"] = {("Available capacity (h)", ""): _number(float(sum(r["available"] for r in weeks))),
                     **{("Assembly (bikes)", j): sum(r["assembled"][j] for r in weeks) for j in MODELS},
                     **{("Stock at the end of the week (bikes)", j): "" for j in MODELS},
                     ("Assembly (h)", ""): fixed(sum(r["assembly hours"] for r in weeks)),
                     ("Setups (h)", ""): fixed(sum(r["setup hours"] for r in weeks)),
                     ("Capacity overload (h)", ""): fixed(sum(r["overload"] for r in weeks))}
    table = pd.DataFrame(rows).T.rename_axis("Week")
    table.columns = pd.MultiIndex.from_tuples(table.columns)
    return table


@_light
def _lots_figure(plant: str, plan: dict) -> None:
    """Above: the lots, the bikes assembled in each week stacked by model. Below:
    the stock at the end of each week stacked by model, with the storage capacity
    and the least stock at the end of each month."""
    fig, (above, below) = plt.subplots(2, 1, figsize=(13, 6.6), sharex=True)
    colours = plt.get_cmap("tab10")
    for ax, key in ((above, "assembled"), (below, "stock")):
        bottom = [0] * len(WEEKS)
        for k, j in enumerate(MODELS):
            values = [plan["weeks"][w][key][j] for w in WEEKS]
            ax.bar(WEEKS, values, 0.75, bottom=bottom, color=colours(k), label=j)
            for w, v, b in zip(WEEKS, values, bottom):
                if v >= 4:
                    ax.text(w, b + v / 2, _number(v), ha="center", va="center", fontsize=6.5, color="white")
            bottom = [b + v for b, v in zip(bottom, values)]
        ax.set_ylim(0, max(max(bottom), (plan["storage"] or 0) if key == "stock" else 0, 1) * 1.15)
        for weeks in plan_weeks().values():
            ax.axvline(weeks[-1] + 0.5, color="0.6", lw=0.8, ls=":")
        ax.spines[["top", "right"]].set_visible(False)
    if plan["storage"] is not None:
        below.axhline(plan["storage"], color="black", ls="--", lw=1, label="storage capacity")
    for t, weeks in plan_weeks().items():
        total = sum(plan["least"][t].values())
        below.plot([weeks[-1] - 0.45, weeks[-1] + 0.45], [total, total], color="black", lw=2.6,
                   label="least stock, all models" if t == T[0] else None)
    above.set_title(f"{_name(plant)}: lots, the bikes assembled in each week by model; each block of colour is one "
                    "lot", fontsize=10)
    above.set_ylabel("Assembly (bikes)")
    above.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    below.set_title(f"{_name(plant)}: stock at the end of each week, by model", fontsize=10)
    below.set_ylabel("Stock (bikes)")
    below.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    below.set_xticks(WEEKS)
    below.tick_params(labelsize=7)
    below.set_xlabel("Week")
    fig.tight_layout()
    plt.show()


def _show_plan(plant: str, plan: dict, show_tables: bool, base: dict | None = None,
               base_label: str = "hours with the data of the case") -> None:
    """A weekly lot plan in one table or, without ``show_tables``, in the figure of
    its lots and stock and the figure of its hours (with those of ``base`` as a
    dashed line)."""
    if show_tables:
        _display(_plan_by_model(plan))
    else:
        _lots_figure(plant, plan)
        _hours_figure({plant: plan}, {plant: base} if base else None, base_label)


def hours_table(plans: dict) -> pd.DataFrame:
    """Table 13: the hours of the line of each plant, by month."""
    rows = {}
    for f, plan in plans.items():
        for t, row in line_hours(plan).items():
            rows[f, t] = {"Weeks": row["weeks"], "Available capacity (h)": _number(float(row["available"])),
                          "Assembly (h)": fixed(row["assembly hours"]), "Setups (h)": fixed(row["setup hours"]),
                          "Capacity overload (h)": fixed(row["overload"]), "Spare capacity (h)": fixed(row["spare"]),
                          "Capacity overload (%)": fixed(100 * row["overload share"], 1)}
    return pd.DataFrame(rows).T.rename_axis(["Plant", "Month"])


def _no_plan(plant: str, plan: dict) -> bool:
    if plan is not None and "no plan" in plan:
        print(f"{plant}: the plan of {plan['no plan']} has no solution: the least stock at the end of the month "
              "does not fit in the storage capacity.")
        return True
    return False


def show_weekly_plan(plant: str = "Plant 1", check: bool = False, show_tables: bool = False) -> dict | None:
    """The weekly lot plan of a plant and its setup and holding cost: the figures
    of its lots, its stock and its hours or, with ``show_tables``, one table (Tables
    10 to 12). With ``check``, whether another plan of some month has the same
    costs."""
    plant = _plant(plant)
    plan = weekly_plan(plant, check=check)
    if _no_plan(plant, plan):
        return None
    print(f"{_name(plant)}: setup and holding cost of the six months {fixed(plan['cost'])} €.")
    if check:
        print("Months with another optimal plan: "
              + (", ".join(plan["other plans"]) if plan["other plans"] else "none") + ".")
    _show_plan(plant, plan, show_tables)
    return plan


@_light
def _hours_figure(plans: dict, base_plans: dict | None = None,
                  base_label: str = "hours with the data of the case") -> None:
    """For each plant, the hours of assembly and of setups of each week against its
    available capacity and, below, the capacity overload of each week in red, on its
    own scale, so that an overload of a few minutes can be read. ``base_plans``,
    drawn as a dashed line with ``base_label``, gives the hours of other plans to
    compare."""
    fig, axes = plt.subplots(2 * len(plans), 1, figsize=(11, 4.6 * len(plans)), squeeze=False,
                             gridspec_kw={"height_ratios": [3, 1.3] * len(plans)})
    for k, (f, plan) in enumerate(plans.items()):
        ax, ax_over = axes[2 * k, 0], axes[2 * k + 1, 0]
        rows = [plan["weeks"][w] for w in WEEKS]
        assembly = [float(r["assembly hours"]) for r in rows]
        setups = [float(r["setup hours"]) for r in rows]
        ax.bar(WEEKS, assembly, color=COLOURS[f], width=0.75, label="assembly")
        ax.bar(WEEKS, setups, bottom=assembly, color=COLOURS[f], alpha=0.45, width=0.75, label="setups")
        ax.step([w - 0.5 for w in WEEKS] + [WEEKS[-1] + 0.5],
                [float(r["available"]) for r in rows] + [float(rows[-1]["available"])],
                where="post", color="black", lw=1.2, label="available capacity")
        overload = [float(r["overload"]) for r in rows]
        ax_over.bar(WEEKS, overload, color=SHORT, width=0.75)
        for w, v in zip(WEEKS, overload):
            if v > 0:
                ax_over.text(w, v, fixed(v, 2), ha="center", va="bottom", fontsize=6.5, color=SHORT)
        if not any(overload):
            ax_over.text(0.5, 0.5, "no capacity overload in any week", transform=ax_over.transAxes,
                         ha="center", va="center", fontsize=8, color="0.4")
        ax_over.set_ylim(0, max(1.0, 1.35 * max(overload)))
        ax_over.set_ylabel("Capacity\noverload (h)")
        if base_plans and f in base_plans:
            ax.plot(WEEKS, [float(r["assembly hours"] + r["setup hours"]) for r in
                            (base_plans[f]["weeks"][w] for w in WEEKS)],
                    color="0.35", lw=1, ls="--", marker=".", label=base_label)
        for a in (ax, ax_over):
            for weeks in plan_weeks().values():
                a.axvline(weeks[-1] + 0.5, color="0.6", lw=0.8, ls=":")
            a.set_xticks(WEEKS)
            a.spines[["top", "right"]].set_visible(False)
        top = max(float(r["available"] + r["overload"]) for r in rows)
        ax.set_ylim(0, max(62, 1.25 * top + 4))
        ax.set_ylabel("Hours of the line (h)")
        ax.set_title(f"{f}: hours of each week; dotted lines at the end of each month", fontsize=10)
        ax.legend(fontsize=7, ncol=4, loc="upper left")
        ax_over.set_title(f"{f}: capacity overload of each week (h)", fontsize=9)
        ax_over.set_xlabel("Week")
    fig.tight_layout()
    plt.show()


def _bar_labels(ax, xs, values, decimals: int = 2, colour: str = "black") -> None:
    top = ax.get_ylim()[1]
    for x, v in zip(xs, values):
        if v > 0:
            ax.text(x, v + top * 0.01, fixed(v, decimals), ha="center", va="bottom", fontsize=6.5, color=colour,
                    rotation=90)


@_light
def _monthly_hours_figure(plans: dict) -> None:
    """For each plant, the hours of its line in each month: assembly and setups,
    then the spare capacity up to the available capacity, and the capacity
    overload above it, with its share of the available capacity (Table 13)."""
    fig, axes = plt.subplots(1, len(plans), figsize=(15, 4.6), sharey=True, squeeze=False)
    x = range(len(T))
    for ax, (f, plan) in zip(axes[0], plans.items()):
        hours = line_hours(plan)
        assembly = [float(hours[t]["assembly hours"]) for t in T]
        setups = [float(hours[t]["setup hours"]) for t in T]
        spare = [float(hours[t]["spare"]) for t in T]
        over = [float(hours[t]["overload"]) for t in T]
        ax.bar(x, assembly, 0.62, color=COLOURS[f], label="assembly")
        ax.bar(x, setups, 0.62, bottom=assembly, color=COLOURS[f], alpha=0.45, label="setups")
        ax.bar(x, spare, 0.62, bottom=[a + s_ for a, s_ in zip(assembly, setups)], color="white",
               edgecolor="0.5", hatch="///", lw=0.6, label="spare capacity")
        for i, t in enumerate(T):
            available = float(hours[t]["available"])
            ax.plot([i - 0.38, i + 0.38], [available, available], color="black", lw=1.4,
                    label="available capacity" if i == 0 else None)
            if over[i] > 0:
                ax.text(i, assembly[i] + setups[i] + 3, f"+{fixed(over[i])} h\n{fixed(100 * hours[t]['overload share'], 1)} %",
                        ha="center", va="bottom", fontsize=7, color=SHORT)
        ax.set_xticks(list(x), T)
        ax.set_ylim(0, 250)
        ax.set_title(f"{_name(f)}\ncapacity overload of the six months: {fixed(hours['Six months']['overload'])} h",
                     fontsize=10)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].set_ylabel("Hours of the line in the month (h)")
    axes[0, -1].legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.suptitle("Capacity overload and spare capacity of each plant, by month", fontsize=11)
    fig.tight_layout()
    plt.show()


@_light
def _limit_figure(plant: str, case: dict) -> None:
    """For each model, the lots of each week of the plan of the model (bars) and of
    the expected plan (black marks) in a limit case of step 7."""
    model, expected = case["model"], case["expected"]
    fig, axes = plt.subplots(len(MODELS), 1, figsize=(13, 8.4), sharex=True)
    colours = plt.get_cmap("tab10")
    for k, (ax, j) in enumerate(zip(axes, MODELS)):
        lots = [model["weeks"][w]["assembled"][j] for w in WEEKS]
        known = [expected["weeks"][w]["assembled"][j] for w in WEEKS]
        ax.bar(WEEKS, lots, 0.75, color=colours(k), label="plan of the model")
        ax.scatter([w for w, v in zip(WEEKS, known) if v > 0], [v for v in known if v > 0], marker="_", s=260,
                   linewidths=2.4, color="black", zorder=3, label="expected plan")
        for w, v in zip(WEEKS, lots):
            if v > 0:
                ax.text(w, v, _number(v), ha="center", va="bottom", fontsize=6.5)
        for weeks in plan_weeks().values():
            ax.axvline(weeks[-1] + 0.5, color="0.6", lw=0.8, ls=":")
        ax.set_ylim(0, max(lots + known + [1]) * 1.3)
        ax.set_ylabel(f"{j}\n(bikes)", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    axes[0].set_title(f"{_name(plant)}: lots of each model, the bikes assembled in each week; dotted lines at the end "
                      "of each month", fontsize=10)
    axes[-1].set_xticks(WEEKS)
    axes[-1].set_xlabel("Week")
    fig.tight_layout()
    plt.show()


def _limit_table(case: dict) -> pd.DataFrame:
    """The lots of each week of the plan of the model and of the expected plan in a
    limit case of step 7, one column for each model."""
    rows = {w: {**{("Assembly, plan of the model (bikes)", j): case["model"]["weeks"][w]["assembled"][j]
                   for j in MODELS},
                **{("Assembly, expected plan (bikes)", j): case["expected"]["weeks"][w]["assembled"][j]
                   for j in MODELS}} for w in WEEKS}
    table = pd.DataFrame(rows).T.rename_axis("Week")
    table.columns = pd.MultiIndex.from_tuples(table.columns)
    return table


@_light
def _runs_figure(plans: dict) -> None:
    """For each plant, the capacity overload (above) and the spare capacity (below)
    of each month in each run (Tables 14 and 15)."""
    fig, axes = plt.subplots(2, len(PLANTS), figsize=(16, 7.4), squeeze=False)
    colours = plt.get_cmap("Set1")
    width = 0.8 / len(RUNS)
    for row, key, label in ((0, "overload", "Capacity overload (h)"), (1, "spare", "Spare capacity (h)")):
        for col, f in enumerate(PLANTS):
            ax = axes[row, col]
            top = max([float(line_hours(p)[t][key]) for (g, _), p in plans.items() if g == f for t in T] + [1])
            for k, name in enumerate(RUNS):
                if (f, name) not in plans:
                    continue
                hours = line_hours(plans[f, name])
                ax.bar([i - 0.4 + width * (k + 0.5) for i in range(len(T))], [float(hours[t][key]) for t in T],
                       width, color="0.3" if name == "As planned" else colours(k),
                       label=name if (row, col) == (0, 1) else None)
            ax.set_ylim(0, top * (1.75 if top > 1 else 1.1))
            totals = [f"{name}: {fixed(line_hours(plans[f, name])['Six months'][key])} h" for name in RUNS
                      if (f, name) in plans]
            ax.text(1.0, 1.0, "Six months\n" + "\n".join(totals), transform=ax.transAxes, ha="right", va="top",
                    fontsize=6.5, bbox={"facecolor": "white", "edgecolor": "0.7", "lw": 0.5})
            if top == 1:
                ax.text(0.5, 0.5, f"no {label.split(' (')[0].lower()} in any run", transform=ax.transAxes,
                        ha="center", va="center", fontsize=9, color="0.4")
            ax.set_xticks(range(len(T)), T)
            ax.set_title(f"{_name(f)}: {label.lower()}", fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
        axes[row, 0].set_ylabel(label)
    fig.suptitle("Weekly plans under the assumptions of the master plan: each run, by plant and month", fontsize=11)
    fig.legend(fontsize=8, loc="upper center", ncol=len(RUNS), bbox_to_anchor=(0.5, 0.95), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    plt.show()


def show_line_hours(show_tables: bool = False) -> dict:
    """The capacity overload and the spare capacity of the three plants by month:
    the figure of each month or, with ``show_tables``, Table 13."""
    plans = {f: weekly_plan(f) for f in PLANTS}
    if show_tables:
        _display(hours_table(plans))
    else:
        _monthly_hours_figure(plans)
    return plans


def show_limit_case(plant: str = "Plant 1", case: str = LIMIT_CASES[0], show_tables: bool = False) -> dict:
    """A limit case of step 7: for the three plants, whether the plan of the model
    is the expected plan; for one plant, the lots of the two plans and the lots and
    stock of the plan of the model, in figures or, with ``show_tables``, in
    tables."""
    plant = _plant(plant)
    if case == LIMIT_CASES[0]:
        print(f"Limit case A: holding cost {_number(LIMIT_HOLDING)} €/(bike·week) for every model; available "
              f"capacity {_number(LIMIT_CAPACITY)} h in every week.")
    elif case == LIMIT_CASES[1]:
        cost = setup_cost({j: LIMIT_SETUP_TIME for j in MODELS})[MODELS[0]]
        print(f"Limit case B: setup time {_number(LIMIT_SETUP_TIME)} h and setup cost {fixed(cost, 0)} € for every "
              f"model; available capacity {_number(LIMIT_CAPACITY)} h in every week; no limit on the storage "
              "capacity.")
    cases = {f: limit_case(f, case) for f in PLANTS}
    for f, result in cases.items():
        overload = sum(row["overload"] for row in result["model"]["weeks"].values())
        verdict = ("is the expected plan in all 26 weeks" if not result["different weeks"] else
                   "differs from the expected plan in weeks " + ", ".join(map(str, result["different weeks"])))
        print(f"{_name(f)}: the plan of the model {verdict}; capacity overload {fixed(overload)} h.")
    result = cases[plant]
    if show_tables:
        _display(_limit_table(result))
        _display(_plan_by_model(result["model"]))
    else:
        _limit_figure(plant, result)
        _lots_figure(plant, result["model"])
    return result


STANDARD_DAYS = 20   # working days of every month in the master plan
ASSUMPTION_PLANTS = PLANTS[:2]   # the plants that assemble at their capacity in every month


def master_plan_hours(plant: str) -> dict:
    """The hours of a month of the master plan at a plant: the available capacity of
    a standard month of 20 working days; the assembly of its capacity in bikes at the
    average assembly time of the six-month product mix; and what is left of the
    available capacity for setups (h)."""
    mix = _base()["six-month mix"]
    available = Fraction(STANDARD_DAYS * HOURS_PER_DAY)
    assembly = K[plant][T[0]] * sum(mix[j] * exact(ASSEMBLY_TIME[plant][j]) for j in MODELS)
    return {"available": available, "assembly hours": assembly, "setup hours": available - assembly}


@_light
def _assumptions_figure(plans: dict) -> None:
    """For plants 1 and 2 and each month, the hours that the master plan assumes
    (grey) next to those that the weekly plans need (colour): assembly, setups and
    available capacity."""
    fig, axes = plt.subplots(1, len(ASSUMPTION_PLANTS), figsize=(14, 5.0), sharey=True, squeeze=False)
    for ax, f in zip(axes[0], ASSUMPTION_PLANTS):
        mp = {k: float(v) for k, v in master_plan_hours(f).items()}
        hours = line_hours(plans[f])
        for i, t in enumerate(T):
            ax.bar(i - 0.2, mp["assembly hours"], 0.38, color="0.7",
                   label="master plan: assembly" if i == 0 else None)
            ax.bar(i - 0.2, mp["setup hours"], 0.38, bottom=mp["assembly hours"], color="0.88", hatch="///",
                   edgecolor="0.5", lw=0.6, label="master plan: setups" if i == 0 else None)
            ax.plot([i - 0.39, i - 0.01], [mp["available"]] * 2, color="0.3", lw=1.4, ls="--",
                    label="master plan: available capacity, 20 working days" if i == 0 else None)
            assembly, setups = float(hours[t]["assembly hours"]), float(hours[t]["setup hours"])
            ax.bar(i + 0.2, assembly, 0.38, color=COLOURS[f], label="weekly plans: assembly" if i == 0 else None)
            ax.bar(i + 0.2, setups, 0.38, bottom=assembly, color=COLOURS[f], alpha=0.45,
                   label="weekly plans: setups" if i == 0 else None)
            ax.plot([i + 0.01, i + 0.39], [float(hours[t]["available"])] * 2, color="black", lw=1.6,
                    label="weekly plans: available capacity" if i == 0 else None)
            ax.text(i - 0.2, mp["assembly hours"] + mp["setup hours"] / 2, fixed(mp["setup hours"], 0),
                    ha="center", va="center", fontsize=7)
            ax.text(i + 0.2, assembly + setups / 2, fixed(setups, 1), ha="center", va="center", fontsize=7)
        ax.set_xticks(range(len(T)), T)
        ax.set_ylim(0, 240)
        ax.set_title(f"{_name(f)}: master plan {fixed(mp['assembly hours'], 0)} h of assembly and "
                     f"{fixed(mp['setup hours'], 0)} h of setups a month", fontsize=10)
        ax.legend(fontsize=7.5, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.32), frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0, 0].set_ylabel("Hours of the line in the month (h)")
    fig.suptitle("Hours of a month assumed by the master plan (grey) and needed by the weekly plans (colour); "
                 "setup hours written in the bars", fontsize=11)
    fig.tight_layout()
    plt.show()


def _assumptions_table(plans: dict) -> pd.DataFrame:
    """The hours of each month assumed by the master plan and needed by the weekly
    plans, at plants 1 and 2."""
    rows = {}
    for f in ASSUMPTION_PLANTS:
        mp = master_plan_hours(f)
        hours = line_hours(plans[f])
        for t in T:
            rows[f, t] = {("Available capacity (h)", "Master plan"): fixed(mp["available"], 0),
                          ("Available capacity (h)", "Weekly plans"): fixed(hours[t]["available"], 0),
                          ("Assembly (h)", "Master plan"): fixed(mp["assembly hours"]),
                          ("Assembly (h)", "Weekly plans"): fixed(hours[t]["assembly hours"]),
                          ("Setups (h)", "Master plan"): fixed(mp["setup hours"]),
                          ("Setups (h)", "Weekly plans"): fixed(hours[t]["setup hours"])}
    table = pd.DataFrame(rows).T.rename_axis(["Plant", "Month"])
    table.columns = pd.MultiIndex.from_tuples(table.columns)
    return table


def _run_rows(plans: dict, key: str) -> pd.DataFrame:
    rows = {}
    for (f, name), plan in plans.items():
        hours = line_hours(plan)
        rows[f, name] = {t: fixed(hours[t][key]) for t in hours}
    return pd.DataFrame(rows).T.rename_axis(["Plant", "Run"])


def show_runs(show_tables: bool = False) -> dict:
    """The weekly plans of the three plants for the six months in each run of part
    d): the capacity overload (Table 14) and the spare capacity (Table 15) of each
    month, in a figure or, with ``show_tables``, in tables, which also give the six
    months. A line shows which run is being solved."""
    plans = {}
    for k, name in enumerate(RUNS, start=1):
        print(f"Solving the weekly plans of the three plants, run {k} of {len(RUNS)}: {name}…", flush=True)
        for f in PLANTS:
            plan = run(f, name)
            if plan is not None:
                plans[f, name] = plan
    as_planned = {f: plans[f, "As planned"] for f in PLANTS}
    if show_tables:
        print("Hours of each month assumed by the master plan and needed by the weekly plans.")
        _display(_assumptions_table(as_planned))
        print("Capacity overload (h) of each plant, by month, in each run.")
        _display(_run_rows(plans, "overload"))
        print("Spare capacity (h) of each plant, by month, in each run.")
        _display(_run_rows(plans, "spare"))
    else:
        _assumptions_figure(as_planned)
        _runs_figure(plans)
    return plans
