"""M2 · Central warehouse (central_warehouse.md): the model of plant_stock.md (M1)
with a central warehouse that receives the shipments of the plants and delivers
the orders, storage capacities at the plants and at the warehouse, and backorders,
written with PuLP and solved with HiGHS; and what the notebook
central_warehouse.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the plants, the warehouse and forecast 3;
2. ``warehouse_plan``: the plan with forecast 3;
3. ``backorders_at_the_end_test``, ``plant_storage_test``, ``backorder_cost_test``
   and ``warehouse_storage_test``: the plan when one datum changes.

A capacity is given as capacity[f][t] (bikes/month), a demand as demand[t]
(bikes/month), and holding costs, storage capacities and stocks of the plants as
dicts by plant. ``final=None`` solves the model without the required ending stock,
and ``owed_end=None`` without the limit on the backorders at the end of the horizon.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .data import (F, FORECAST_3, FORECASTS, K, K_h, K_h_w, T, b_0, b_max, c, c_b, c_h, c_h_w, h_0,
                   h_end, h_w_0, h_w_end)
from .model import TOL, _constraints, _optimal
from .show import COLOURS, SHORT, _display, _euros, _european_axes, _light, _number

FORECAST = "Forecast 3"                   # M2 is solved with forecast 3
DEMAND = FORECAST_3
WAREHOUSE = "Warehouse"
WAREHOUSE_COLOUR = "tab:gray"
SEVERAL = ("With these data the model has several optimal plans with the same cost; "
           "the table shows one of them.")


def _name(f: str, t: str) -> str:
    return f"{f.replace(' ', '')}_{t}"


def build(demand: dict = DEMAND, months=T, holding: dict = c_h, plant_storage: dict = K_h,
          warehouse_holding: float = c_h_w, warehouse_storage: float = K_h_w, initial: dict = h_0,
          warehouse_initial: float = h_w_0, final: dict | None = h_end, warehouse_final: float = h_w_end,
          late_cost: float = c_b, owed_initial: float = b_0, owed_end: float | None = b_max,
          capacity: dict = K, plants=F):
    """The model of M2, not solved. Returns the model, a dict of its variables by
    kind ("p", "x", "h" by (f, t); "h_w", "s", "b" by t) and the cost expression."""
    model = pulp.LpProblem("central_warehouse", pulp.LpMinimize)
    # p[f, t] = bikes assembled, x[f, t] = bikes shipped from plant f to the warehouse
    # in month t (bikes/month); h[f, t] = bikes in stock at plant f at the end of month t
    p = {(f, t): model.add_variable(f"p_{_name(f, t)}", lowBound=0) for f in plants for t in months}
    x = {(f, t): model.add_variable(f"x_{_name(f, t)}", lowBound=0) for f in plants for t in months}
    h = {(f, t): model.add_variable(f"h_{_name(f, t)}", lowBound=0) for f in plants for t in months}
    # h_w[t] = bikes in stock at the warehouse at the end of month t (bikes);
    # s[t] = deliveries: bikes the warehouse delivers in month t to orders of that
    # month or to backorders (bikes/month); b[t] = backorders at the end of month t:
    # orders received and not yet delivered (bikes)
    h_w = {t: model.add_variable(f"h_w_{t}", lowBound=0) for t in months}
    s = {t: model.add_variable(f"s_{t}", lowBound=0) for t in months}
    b = {t: model.add_variable(f"b_{t}", lowBound=0) for t in months}
    # Minimise the assembly, holding and backorder cost
    cost = pulp.lpSum(c[f] * p[f, t] + holding[f] * h[f, t] for f in plants for t in months) \
        + pulp.lpSum(warehouse_holding * h_w[t] + late_cost * b[t] for t in months)
    model += cost
    for f in plants:
        for i, t in enumerate(months):
            before = initial[f] if i == 0 else h[f, months[i - 1]]
            # Stock at the start of the month plus what is assembled is what is
            # shipped plus the stock at the end of the month
            model += (before + p[f, t] == x[f, t] + h[f, t], f"balance_{_name(f, t)}")
            # A plant ships at most what it held at the start of the month plus
            # what it assembles: the stock of the previous month
            model += (x[f, t] <= before + p[f, t], f"shipment_limit_{_name(f, t)}")
            model += (p[f, t] <= capacity[f][t], f"capacity_{_name(f, t)}")
            model += (h[f, t] <= plant_storage[f], f"storage_{_name(f, t)}")
        if final is not None:
            model += (h[f, months[-1]] >= final[f], f"final_stock_{f.replace(' ', '')}")
    for i, t in enumerate(months):
        stock_before = warehouse_initial if i == 0 else h_w[months[i - 1]]
        owed_before = owed_initial if i == 0 else b[months[i - 1]]
        arriving = pulp.lpSum(x[f, t] for f in plants)
        # Stock at the start of the month plus what arrives is what is delivered
        # plus the stock at the end of the month
        model += (stock_before + arriving == s[t] + h_w[t], f"warehouse_balance_{t}")
        # Shipment limit: the warehouse delivers at most what it held at the start of
        # the month plus what arrives: the stock of the previous month
        model += (s[t] <= stock_before + arriving, f"shipment_limit_warehouse_{t}")
        # Backorder balance: backorders at the start of the month plus the orders of
        # the month are the deliveries plus the backorders at the end. Written with
        # the demand on the right, so that its shadow price is what one more order costs
        model += (s[t] + b[t] - owed_before == demand[t], f"orders_{t}")
        model += (h_w[t] <= warehouse_storage, f"warehouse_storage_{t}")
    if owed_end is not None:
        model += (b[months[-1]] <= owed_end, "backorders_at_the_end")
    if final is not None:
        model += (h_w[months[-1]] >= warehouse_final, "final_stock_warehouse")
    return model, {"p": p, "x": x, "h": h, "h_w": h_w, "s": s, "b": b}, cost


def only_optimal(model, variables: list, cost) -> bool | None:
    """True if the model has one optimal solution: with the cost fixed at its optimum,
    every variable has the same minimum and maximum. False if several solutions have
    the optimal cost; None if the model has no solution. The model is changed."""
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    model += (cost <= pulp.value(model.objective) + 1e-6, "optimal_cost")
    for var in variables:
        ends = []
        for sense in (pulp.LpMinimize, pulp.LpMaximize):
            model.sense = sense
            model.setObjective(var)
            model.solve(pulp.HiGHS(msg=False))
            ends.append(var.value())
        if abs(ends[0] - ends[1]) > 1e-3:          # bikes
            return False
    return True


def only_plan(**data) -> bool | None:
    """True if the optimal plan of M2 with the data given (the arguments of ``build``)
    is the only one; False if several plans have the optimal cost; None if the
    model has no solution."""
    model, var, cost = build(**data)
    return only_optimal(model, [v for kind in var.values() for v in kind.values()], cost)


def solve(**data) -> dict | None:
    """Solve M2 with the data given (the arguments of ``build``). Returns the cost
    (EUR); the bikes assembled, shipped to the warehouse and in stock at each plant
    and month; the stock of the warehouse, its deliveries and the backorders each
    month (bikes); the shadow prices of the backorder balance of each month and of
    the storage capacities (EUR/bike). None if the model has no solution."""
    model, var, _ = build(**data)
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    months = list(var["h_w"])
    cons = _constraints(model)
    clean = lambda v: 0.0 if abs(v) < TOL else v      # noqa: E731  (no "-0.0" in tables)
    values = {kind: {key: clean(v.value()) for key, v in var[kind].items()} for kind in var}
    plants = sorted({f for f, _ in var["p"]}, key=F.index)
    return {
        "months": months,
        "cost": pulp.value(model.objective),
        "assembly": values["p"], "shipments": values["x"], "stock": values["h"],
        "warehouse stock": values["h_w"], "served": values["s"], "owed": values["b"],
        "orders price": {t: clean(cons[f"orders_{t}"].pi) for t in months},
        "storage price": {(f, t): clean(cons[f"storage_{_name(f, t)}"].pi) for f in plants for t in months},
        "warehouse storage price": {t: clean(cons[f"warehouse_storage_{t}"].pi) for t in months},
    }


def m1_has_no_solution(demand: dict = DEMAND) -> str | None:
    """Why M1, with stock at the plants only, has no solution for a demand; None if it has one."""
    from . import plant_stock
    if plant_stock.solve(demand=demand) is not None:
        return None
    return plant_stock.why_no_plan(demand=demand)


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def show_data() -> None:
    """Tables 1 to 3 of central_warehouse.md: the plants, the warehouse and the
    backorders, and forecast 3."""
    _display(pd.DataFrame({f: {"Unit assembly cost (€/bike)": c[f],
                               "Capacity (bikes/month, every month)": K[f]["Jan"],
                               "Holding cost (€/(bike·month))": c_h[f],
                               "Storage capacity (bikes)": K_h[f],
                               "Stock at the end of December (bikes)": h_0[f],
                               "Required ending stock (bikes)": h_end[f]} for f in F})
             .T.rename_axis("Plant"))
    _display(pd.DataFrame({WAREHOUSE: {"Holding cost (€/(bike·month))": c_h_w,
                                       "Storage capacity (bikes)": K_h_w,
                                       "Stock at the end of December (bikes)": h_w_0,
                                       "Required ending stock (bikes)": h_w_end,
                                       "Backorder cost (€/(bike·month))": c_b,
                                       "Backorders at the end of December (bikes)": b_0,
                                       "Maximum backorders at the end of the horizon (bikes)": b_max}})
             .rename_axis("Central warehouse"))
    _display(pd.DataFrame({FORECAST: DEMAND}).T.rename_axis("Orders (bikes/month)"))


def _plan_table(solution: dict) -> pd.DataFrame:
    months = solution["months"]
    rows = {}
    for label, key in (("Assembled", "assembly"), ("Shipped to the warehouse", "shipments"),
                       ("Stock at the end of the month", "stock")):
        for f in F:
            rows[label, f] = {t: solution[key][f, t] for t in months}
    for label, key in (("Stock at the end of the month", "warehouse stock"), ("Deliveries", "served"),
                       ("Backorders at the end of the month", "owed")):
        rows[label, WAREHOUSE] = {t: solution[key][t] for t in months}
    return pd.DataFrame(rows).T.rename_axis(["Bikes", "Site"])


@_light
def _figure(solution: dict, demand: dict, capacity: dict = K) -> None:
    """Left: bikes assembled by each plant, with the capacity of the three plants,
    the orders and the deliveries. Right: stock at the plants and at the warehouse
    at the end of each month, and the backorders."""
    months = solution["months"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 3.8))
    x = range(len(months))
    bottom = [0.0] * len(months)
    for f in F:
        values = [solution["assembly"][f, t] for t in months]
        left.bar(x, values, bottom=bottom, color=COLOURS[f], width=0.7, label=f"assembled {f}")
        bottom = [b + v for b, v in zip(bottom, values)]
    left.plot(x, [sum(capacity[f][t] for f in F) for t in months], color="0.4", ls="--", marker="_",
              label="capacity of the three plants")
    left.plot(x, [demand[t] for t in months], color="black", marker="o", label="orders")
    left.plot(x, [solution["served"][t] for t in months], color=SHORT, marker="s", ls=":", label="deliveries")
    left.set_xticks(list(x), months)
    left.set_ylabel("Bikes/month")
    left.set_ylim(0, max(760, max(demand[t] for t in months) * 1.1))
    left.set_title("Bikes assembled, orders and deliveries", fontsize=10)
    left.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False)
    left.spines[["top", "right"]].set_visible(False)

    width = 0.4
    bottom = [0.0] * len(months)
    for f in F:
        values = [solution["stock"][f, t] for t in months]
        right.bar([i - width / 2 for i in x], values, bottom=bottom, color=COLOURS[f], width=width,
                  label=f"stock {f}")
        bottom = [b + v for b, v in zip(bottom, values)]
    values = [solution["warehouse stock"][t] for t in months]
    right.bar([i - width / 2 for i in x], values, bottom=bottom, color=WAREHOUSE_COLOUR, width=width,
              label="stock at the warehouse")
    top = max(b + v for b, v in zip(bottom, values))
    owed = [solution["owed"][t] for t in months]
    right.bar([i + width / 2 for i in x], owed, color="none", edgecolor=SHORT, hatch="///", width=width,
              label="backorders")
    right.set_xticks(list(x), months)
    right.set_ylabel("Bikes at the end of the month")
    right.set_ylim(0, max(300, top * 1.15, max(owed) * 1.15))
    right.set_title("Stock and backorders", fontsize=10)
    right.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False)
    right.spines[["top", "right"]].set_visible(False)
    _european_axes(fig)
    plt.show()


def _report(data: dict, heading: str) -> dict | None:
    """Solve M2 with the data given and show the plan and its cost, whether other
    plans have the same cost, the shadow prices and the figure."""
    solution = solve(**data)
    if solution is None:
        print(f"{heading}: the model has no solution.")
        return None
    months = solution["months"]
    print(f"{heading}: optimal plan, cost {_euros(solution['cost'])}.")
    _display(_plan_table(solution))
    if not only_plan(**data):
        print(SEVERAL)
    print("Shadow price of the backorder balance of each month (€/bike): what one more order that "
          "month costs.")
    _display(pd.DataFrame({t: {"Shadow price (€/bike)": solution["orders price"][t]} for t in months}))
    print("Shadow price of each storage capacity (€/bike): the change in cost with one more bike of "
          "storage capacity (negative: a saving).")
    table = {t: {f: solution["storage price"][f, t] for f in F} for t in months}
    for t in months:
        table[t][WAREHOUSE] = solution["warehouse storage price"][t]
    _display(pd.DataFrame(table).rename_axis("Storage shadow price"))
    _figure(solution, data.get("demand", DEMAND))
    return solution


def warehouse_plan() -> dict | None:
    """The plan with forecast 3; and, first, whether M1 has a plan for it."""
    reason = m1_has_no_solution()
    if reason:
        print(f"M1, with stock at the plants only, has no solution with {FORECAST.lower()}. {reason}")
        print()
    return _report({}, FORECAST)


def backorders_at_the_end_test(limit_backorders_at_the_end: bool = True) -> dict | None:
    """The plan with forecast 3, with or without the limit on the backorders at the end of June."""
    if limit_backorders_at_the_end:
        return _report({}, f"{FORECAST}, no backorders at the end of June")
    solution = _report({"owed_end": None}, f"{FORECAST}, without the limit on the backorders at the end")
    if solution is not None:
        print(f"Backorders at the end of June: {_number(solution['owed'][solution['months'][-1]])} bikes.")
    return solution


def plant_storage_test(storage_plant_1: float = 40) -> dict | None:
    """The plan with the storage capacities of the three plants moved together:
    plant 2 holds 10 bikes less than plant 1, and plant 3 holds 20 less."""
    storage = {"Plant 1": storage_plant_1, "Plant 2": storage_plant_1 - 10, "Plant 3": storage_plant_1 - 20}
    print("Storage capacity of the plants (bikes): "
          + "; ".join(f"{f.lower()} {_number(v)}" for f, v in storage.items()) + ".")
    return _report({"plant_storage": storage}, FORECAST)


def backorder_cost_test(backorder_cost: float = 60) -> dict | None:
    """The plan with forecast 2 and the backorder cost changed."""
    print(f"Backorder cost: {_number(backorder_cost)} €/(bike·month).")
    return _report({"demand": FORECASTS["Forecast 2"], "late_cost": backorder_cost}, "Forecast 2")


def warehouse_storage_test(warehouse_storage: float = 150) -> dict | None:
    """The plan with forecast 3 and the storage capacity of the warehouse changed."""
    print(f"Storage capacity of the warehouse: {_number(warehouse_storage)} bikes.")
    return _report({"warehouse_storage": warehouse_storage}, FORECAST)
