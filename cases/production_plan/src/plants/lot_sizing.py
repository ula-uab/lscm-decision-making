"""Lot sizing at the plants (lot_sizing.md): the weekly plan of each plant, which
checks whether the plant can assemble, week by week and model by model, what the
master plan of M4 (retailers.md) gives it each month. M4 is called, not copied:
it is solved with the orders that the retailers place each month. Written with
PuLP and solved with HiGHS; and what the notebook lot_sizing.ipynb shows.

The computations, each with its data as arguments:

1. ``weekly_orders`` and ``monthly_orders``: the orders of each retailer, by
   model and week, and by month (Table 7);
2. ``master_plan``: M4 with those orders (Table 10);
3. ``seasonal_split``, ``shipment_mix``, ``least_stock`` and
   ``weekly_shipments``: what each plant ships each week and the least stock it
   holds at the end of each month (Tables 10 to 12);
4. ``weekly_plan``: one plan for each month, one after the other, each in the
   two stages of step 6 (Tables 13 to 15);
5. ``lot_for_lot``: the plan of step 7, which assembles each week what it ships;
6. ``line_hours``: assembly, setups, capacity overload and spare capacity by
   month (Table 16);
7. ``run``: the plans of the six months with the data of part d) (Tables 17
   and 18).

Quantities are exact: fractions, not floating point, so that every rounding,
half up, starts from the exact value.

The notebook calls one function per step: ``show_orders``, ``show_master_plan``,
``show_shipments``, ``show_weekly_plan``, ``show_line_hours`` and
``change_test``.
"""

from __future__ import annotations

import functools
import math
from fractions import Fraction

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from . import retailers
from .data import (ARCS_M4, ASSEMBLY_TIME, AVERAGE_ORDERS, CREW_COST, FIRST_BIKE_CHECK, HOLIDAYS, HOURS_PER_DAY,
                   MODELS, MONTH_DAYS, NODES, PLACES_M4, PLANT_STOCK_0, PRODUCT_MIX, RETAILERS, SEASONAL_INDEX,
                   SETUP_TIME, VALUE_FACTOR, WEEK_FACTOR, WEEKS, F, K_h, T, c_h)
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
# 1. Orders (§1, Tables 4 to 7)
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
    bikes), by (r, t): Table 7. The orders accumulated from January are rounded
    half up."""
    by_model = model_orders(weekly)
    retailers_ = sorted({r for r, _, _ in by_model}, key=RETAILERS.index)
    out = {}
    for r in retailers_:
        raw = [sum(by_model[r, j, t] for j in MODELS) for t in T]
        out.update({(r, t): q for t, q in zip(T, _cumulative(raw))})
    return out


# ---------------------------------------------------------------------------
# 2. Master plan: M4 with the orders of Table 7 (§2, Table 10)
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
# 3. Shipments and least stock of each plant (§2, Tables 10 to 12)
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
    """The product mix of the shipments of the plants in each month (Table 11):
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
    week (whole bikes), by (f, j, w), Table 12. The shipments of a month are spread
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
    every week: the bikes that each plant ships in a week (Table 12) split among the
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
    # p = bikes assembled (integer); h = stock at the end of the week; delta = 1 if
    # the model is set up and assembled in the week; o = capacity overload (h)
    p = {(j, w): model.add_variable(f"p_{j}_{w}", lowBound=0, cat="Integer") for j in MODELS for w in weeks}
    h = {(j, w): model.add_variable(f"h_{j}_{w}", lowBound=0) for j in MODELS for w in weeks}
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
    cost (EUR); and, with ``check``, the months in which another plan has the same
    costs. Returns None, with the month, if a month has no plan."""
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
            "other plans": others if check else None}


# ---------------------------------------------------------------------------
# 5. The plan of step 7: each week assembles what it ships
# ---------------------------------------------------------------------------

def lot_for_lot(plant: str, shipments: dict | None = None, least: dict | None = None, assembly: dict | None = None,
                setup: dict | None = None, holding: dict | None = None, capacity: dict | None = None,
                initial: dict | None = None) -> dict:
    """The plan of step 7 at a plant: each week assembles, model by model, what it
    ships less the stock it holds, with a setup of every model it assembles; in the
    week of the end of the month it also assembles what it lacks of the least
    stock. Returns what ``weekly_plan`` returns, evaluated in the model."""
    data = _base()
    shipments = data["shipments"] if shipments is None else shipments
    least = data["least stock"] if least is None else least
    assembly, setup, holding, _, capacity, stock = _plant_data(plant, assembly, setup, holding, 0, capacity, initial)
    stock = dict(stock)
    weeks = {}
    for t, plan_weeks_ in plan_weeks().items():
        for w in plan_weeks_:
            need = {j: shipments[plant, j, w] + (least[plant, t][j] if w == plan_weeks_[-1] else 0) for j in MODELS}
            assembled = {j: max(0, need[j] - stock[j]) for j in MODELS}
            stock = {j: stock[j] + assembled[j] - shipments[plant, j, w] for j in MODELS}
            weeks[w] = _week(stock, assembled, {j: int(assembled[j] > 0) for j in MODELS}, assembly, setup,
                             capacity[w])
    return {"plant": plant, "weeks": weeks, "cost": _cost(weeks, setup, holding), "other plans": None}


# ---------------------------------------------------------------------------
# 6. Hours of the line by month (Table 16)
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
# 7. The runs of part d) (Tables 17 and 18)
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


def orders_table(order: dict) -> pd.DataFrame:
    """Table 7: the orders of each retailer in each month."""
    table = pd.DataFrame({f"{PLACES_M4[r][0]}": {t: order[r, t] for t in T} for r in RETAILERS}).T
    table.loc["All"] = table.sum()
    table["Six months"] = table.sum(axis=1)
    return table.rename_axis("Orders (bikes)")


def show_orders() -> None:
    """The orders of the retailers: the six-month totals by model, and Table 7."""
    data = _base()
    totals = {j: sum(q for (_, i, _), q in data["weekly orders"].items() if i == j) for j in MODELS}
    print("Orders of the 26 weeks, all retailers (bikes): "
          + "; ".join(f"{j} {_number(totals[j])}" for j in MODELS)
          + "; product mix " + "; ".join(f"{fixed(100 * data['six-month mix'][j], 1)} %" for j in MODELS) + ".")
    _display(orders_table(data["orders"]))


def master_plan_table(master: dict, least: dict) -> pd.DataFrame:
    """Table 10: the plan of M4 at each plant and the least stock of each model at
    the end of each month."""
    rows = {}
    for f in PLANTS:
        for t in T:
            rows[f, t] = {"Assembled": _number(float(master["assembled"][f, t])),
                          "Shipped to the network": _number(float(master["shipped"][f, t])),
                          "Stock at the end": _number(float(master["stock"][f, t])),
                          "Least stock at the end": _bikes(least[f, t])}
    return pd.DataFrame(rows).T.rename_axis(["Plant", "Month"])


def show_master_plan() -> None:
    """M4 solved with the orders of Table 7: its cost, Table 10 and the stock of
    the network."""
    data = _base()
    master = data["master"]
    print(f"M4 with the orders of the retailers: cost {_number(master['cost'], 2)} €; backorders "
          f"{_number(float(sum(master['backorders'].values())))} and lost sales "
          f"{_number(float(sum(master['lost sales'].values())))} bikes.")
    _display(master_plan_table(master, data["least stock"]))
    print("Stock of the network, plants and warehouses, at the end of each month (bikes): "
          + "; ".join(f"{t} {_number(float(master['network stock'][t]))}" for t in T) + ".")


def mix_table(mix: dict, split: dict, master: dict) -> pd.DataFrame:
    """Table 11: the product mix of the shipments and the split of the seasonal
    stock, by month (%). A month that ends with no stock has no split."""
    rows = {}
    for j in MODELS:
        rows[f"Shipments, {j}"] = {t: fixed(100 * mix[t][j], 1) for t in T}
    for j in MODELS:
        rows[f"Seasonal stock, {j}"] = {t: fixed(100 * split[t][j], 1) if master["network stock"][t] else "—"
                                        for t in T}
    return pd.DataFrame(rows).T.rename_axis("Product mix (%)")


def shipments_table(shipments: dict, plants=PLANTS) -> pd.DataFrame:
    """Table 12: the shipments of each plant in each week, by model."""
    rows = {w: {f: _bikes({j: shipments[f, j, w] for j in MODELS}) for f in plants} for w in WEEKS}
    rows["Total"] = {f: _bikes({j: sum(shipments[f, j, w] for w in WEEKS) for j in MODELS}) for f in plants}
    return pd.DataFrame(rows).T.rename_axis("Week")


def show_shipments(plant: str = "Plant 1") -> None:
    """The product mix of the shipments (Table 11), the shipments of a plant by
    week and model (its column of Table 12) and its least stock at the end of each
    month, with a figure."""
    plant = _plant(plant)
    data = _base()
    _display(mix_table(data["mix"], data["split"], data["master"]))
    print(f"{plant}: shipments to the network in each week (bikes: {'; '.join(MODELS)}).")
    _display(shipments_table(data["shipments"], [plant]))
    print(f"{plant}: least stock at the end of each month (bikes: {'; '.join(MODELS)}): "
          + "; ".join(f"{t} ({_bikes(data['least stock'][plant, t])})" for t in T) + ".")
    _shipments_figure(plant, data["shipments"])


@_light
def _shipments_figure(plant: str, shipments: dict) -> None:
    fig, ax = plt.subplots(figsize=(11, 3.6))
    bottom = [0] * len(WEEKS)
    colours = plt.get_cmap("tab10")
    for k, j in enumerate(MODELS):
        values = [shipments[plant, j, w] for w in WEEKS]
        ax.bar(WEEKS, values, bottom=bottom, color=colours(k), width=0.75, label=j)
        bottom = [b + v for b, v in zip(bottom, values)]
    for t, weeks in plan_weeks().items():
        ax.axvline(weeks[-1] + 0.5, color="0.6", lw=0.8, ls=":")
        ax.annotate(t, ((weeks[0] + weeks[-1]) / 2, max(bottom) * 1.05), ha="center", fontsize=8)
    ax.set_xticks(WEEKS)
    ax.set_xlabel("Week")
    ax.set_ylabel("Shipments (bikes)")
    ax.set_ylim(0, max(bottom) * 1.15 + 1)
    ax.set_title(f"{plant}: shipments to the network in each week, by model", fontsize=10)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    plt.show()


def plan_table(plan: dict) -> pd.DataFrame:
    """Tables 13 to 15: the weekly lot plan of a plant."""
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


def hours_table(plans: dict) -> pd.DataFrame:
    """Table 16: the hours of the line of each plant, by month."""
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


def show_weekly_plan(plant: str = "Plant 1", check: bool = False) -> dict | None:
    """The weekly lot plan of a plant (Tables 13 to 15), its setup and holding
    cost, and a figure of the hours of each week against the available capacity.
    With ``check``, whether another plan of some month has the same costs."""
    plant = _plant(plant)
    plan = weekly_plan(plant, check=check)
    if _no_plan(plant, plan):
        return None
    print(f"{plant}: setup and holding cost of the six months {fixed(plan['cost'])} €. Bikes by model: "
          f"{'; '.join(MODELS)}.")
    if check:
        print("Another plan has the same capacity overload and the same cost in "
              + (", ".join(plan["other plans"]) if plan["other plans"] else "no month") + ".")
    _display(plan_table(plan))
    _hours_figure({plant: plan})
    return plan


@_light
def _hours_figure(plans: dict, base_plans: dict | None = None,
                  base_label: str = "hours with the data of the case") -> None:
    """For each plant, the hours of assembly and of setups of each week against its
    available capacity; the capacity overload in red. ``base_plans``, drawn as a
    dashed line with ``base_label``, gives the hours of other plans to compare."""
    fig, axes = plt.subplots(len(plans), 1, figsize=(11, 3.2 * len(plans)), squeeze=False)
    for ax, (f, plan) in zip(axes[:, 0], plans.items()):
        rows = [plan["weeks"][w] for w in WEEKS]
        assembly = [float(r["assembly hours"]) for r in rows]
        setups = [float(r["setup hours"]) for r in rows]
        ax.bar(WEEKS, assembly, color=COLOURS[f], width=0.75, label="assembly")
        ax.bar(WEEKS, setups, bottom=assembly, color=COLOURS[f], alpha=0.45, width=0.75, label="setups")
        ax.step([w - 0.5 for w in WEEKS] + [WEEKS[-1] + 0.5],
                [float(r["available"]) for r in rows] + [float(rows[-1]["available"])],
                where="post", color="black", lw=1.2, label="available capacity")
        over = [w for w, r in zip(WEEKS, rows) if r["overload"] > 0]
        ax.scatter(over, [float(plan["weeks"][w]["available"] + plan["weeks"][w]["overload"]) + 1.5 for w in over],
                   color=SHORT, marker="v", s=18, label="capacity overload")
        if base_plans and f in base_plans:
            ax.plot(WEEKS, [float(r["assembly hours"] + r["setup hours"]) for r in
                            (base_plans[f]["weeks"][w] for w in WEEKS)],
                    color="0.35", lw=1, ls="--", marker=".", label=base_label)
        for weeks in plan_weeks().values():
            ax.axvline(weeks[-1] + 0.5, color="0.6", lw=0.8, ls=":")
        ax.set_xticks(WEEKS)
        top = max(float(r["available"] + r["overload"]) for r in rows)
        ax.set_ylim(0, max(62, 1.25 * top + 4))
        ax.set_ylabel("Hours of the line (h)")
        ax.set_title(f"{f}: hours of each week; dotted lines at the end of each month", fontsize=10)
        ax.legend(fontsize=7, ncol=5, loc="upper left")
        ax.spines[["top", "right"]].set_visible(False)
    axes[-1, 0].set_xlabel("Week")
    fig.tight_layout()
    plt.show()


def show_line_hours() -> dict:
    """The hours of the line of the three plants by month (Table 16), with the
    figure of the hours of each week."""
    plans = {f: weekly_plan(f) for f in PLANTS}
    _display(hours_table(plans))
    _hours_figure(plans)
    return plans


def change_test(plant: str = "Plant 2", no_holidays: bool = False, extra_holiday_week: int = 0,
                model: str = "Cargo", setup_time: float = 0, assembly_time: float = 0,
                storage: int = 0) -> dict | None:
    """The weekly plans of a plant for the six months with some of its data
    changed: no holidays, or one more holiday on the Wednesday of a week; the
    setup time and the assembly time of one model; and the storage capacity. A 0
    keeps the datum of the case. The setup cost follows the setup time. Shows the
    hours of the line by month, next to those with the data of the case, and the
    weekly plan."""
    plant = _plant(plant)
    if model not in MODELS:
        raise ValueError(f"The model must be one of {', '.join(MODELS)}.")
    holidays = {f: list(v) for f, v in HOLIDAYS.items()}
    changes = []
    if no_holidays:
        holidays[plant] = []
        changes.append("no holidays")
    if extra_holiday_week:
        if not 1 <= extra_holiday_week <= len(WEEKS):
            raise ValueError(f"The week must be between 1 and {len(WEEKS)}.")
        day = 7 * (extra_holiday_week - 1) + 2
        month = _month_of(day)
        holidays[plant].append((month, day - _day(month, 1) + 1))
        changes.append(f"one more holiday in week {extra_holiday_week}")
    setup = dict(SETUP_TIME[plant])
    assembly = dict(ASSEMBLY_TIME[plant])
    if setup_time and exact(setup_time) != exact(setup[model]):
        changes.append(f"setup time of {model} {_number(setup_time)} h instead of {_number(setup[model])} h")
        setup[model] = setup_time
    if assembly_time and exact(assembly_time) != exact(assembly[model]):
        changes.append(f"assembly time of {model} {_number(assembly_time, 3)} h/bike instead of "
                       f"{_number(assembly[model], 3)} h/bike")
        assembly[model] = assembly_time
    if storage and storage != K_h[plant]:
        changes.append(f"storage capacity {_number(storage)} bikes instead of {_number(K_h[plant])}")
    else:
        storage = None
    print(f"{plant}: " + ("; ".join(changes) if changes else "the data of the case") + ".")
    plan = weekly_plan(plant, assembly=assembly, setup=setup, storage=storage,
                       capacity=available_capacity(plant, holidays))
    if _no_plan(plant, plan):
        return None
    before = weekly_plan(plant)
    new, old = line_hours(plan), line_hours(before)
    rows = {}
    for t in new:
        rows[t] = {"Available capacity (h)": _number(float(new[t]["available"])),
                   "Setups (h)": fixed(new[t]["setup hours"]),
                   "Capacity overload (h)": fixed(new[t]["overload"]),
                   "Capacity overload, data of the case (h)": fixed(old[t]["overload"]),
                   "Spare capacity (h)": fixed(new[t]["spare"]),
                   "Spare capacity, data of the case (h)": fixed(old[t]["spare"])}
    print(f"Setup and holding cost of the six months: {fixed(plan['cost'])} €; with the data of the case, "
          f"{fixed(before['cost'])} €.")
    _display(pd.DataFrame(rows).T.rename_axis("Month"))
    _display(plan_table(plan))
    _hours_figure({plant: plan}, {plant: before})
    return plan


def show_reference_plan(plant: str = "Plant 1") -> dict:
    """The plan of reference of step 7 against the plans of the model: the capacity
    overload and the setup and holding cost of the six months at the three plants;
    and the weekly plan of reference of one plant, in the form of Tables 13 to 15,
    with a figure of its hours next to those of the plan of the model."""
    plant = _plant(plant)
    model = {f: weekly_plan(f) for f in PLANTS}
    reference = {f: lot_for_lot(f) for f in PLANTS}
    rows = {f: {"Capacity overload, plan of reference (h)": fixed(line_hours(reference[f])["Six months"]["overload"]),
                "Capacity overload, plan of the model (h)": fixed(line_hours(model[f])["Six months"]["overload"]),
                "Setup and holding cost, plan of reference (€)": fixed(reference[f]["cost"]),
                "Setup and holding cost, plan of the model (€)": fixed(model[f]["cost"])} for f in PLANTS}
    _display(pd.DataFrame(rows).T.rename_axis("Six months"))
    print(f"{plant}: weekly plan of reference. Bikes by model: {'; '.join(MODELS)}.")
    _display(plan_table(reference[plant]))
    _hours_figure({plant: reference[plant]}, {plant: model[plant]}, "hours of the plan of the model")
    return reference[plant]


def _run_rows(plans: dict, key: str) -> pd.DataFrame:
    rows = {}
    for (f, name), plan in plans.items():
        hours = line_hours(plan)
        rows[f, name] = {t: fixed(hours[t][key]) for t in hours}
    return pd.DataFrame(rows).T.rename_axis(["Plant", "Run"])


def show_runs(plant: str = "none", run_name: str = "As planned") -> dict:
    """The weekly plans of the three plants for the six months in each run of part
    d): the capacity overload (Table 17) and the spare capacity
    (Table 18) of each month, and the months in which another plan has the same
    capacity overload and the same cost. With a plant and a run, also the weekly
    plan of that plant in that run, with a figure of its hours next to those of the
    plan with the data of the case. ``run_name`` is one of ``RUNS``."""
    if run_name not in RUNS:
        raise ValueError(f"The run must be one of {', '.join(RUNS)}.")
    plans = {}
    for f in PLANTS:
        for name in RUNS:
            plan = run(f, name, check=True)
            if plan is not None:
                plans[f, name] = plan
    print("Capacity overload (h) of each plant, by month, in each run.")
    _display(_run_rows(plans, "overload"))
    print("Spare capacity (h) of each plant, by month, in each run.")
    _display(_run_rows(plans, "spare"))
    others = [f"{f}, {name}: {', '.join(p['other plans'])}" for (f, name), p in plans.items() if p["other plans"]]
    print("Months in which another plan has the same capacity overload and the same cost: "
          + ("; ".join(others) if others else "none") + ".")
    if plant != "none":
        plant = _plant(plant)
        if (plant, run_name) not in plans:
            print(f"{plant} has no run «{run_name}»: its setup times are those of plant 1.")
            return plans
        print(f"{plant}, {run_name}: setup and holding cost of the six months {fixed(plans[plant, run_name]['cost'])} €. "
              f"Bikes by model: {'; '.join(MODELS)}.")
        _display(plan_table(plans[plant, run_name]))
        _hours_figure({plant: plans[plant, run_name]}, {plant: plans[plant, "As planned"]})
    return plans
