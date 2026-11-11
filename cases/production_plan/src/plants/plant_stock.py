"""M1 · Stock at the plants (plant_stock.md): the model of production_plan.md (M0)
with stock at each plant from one month to the next, written with PuLP and solved
with HiGHS, and what the notebook plant_stock.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the plants with their costs, capacities and stocks, and forecast 2;
2. ``stock_plan``: the plan with forecast 2, with or without the required final stock;
3. ``holding_cost_test``, ``demand_test``, ``horizon_test`` and ``final_stock_test``:
   the plan when one datum changes.

Steps 2 and 3 show figures or, with ``show_tables``, the same data in tables.

A capacity is given as capacity[f][t] (bikes/month), a demand as demand[t]
(bikes/month), and holding costs and stocks as dicts by plant. ``final=None``
solves the model without the required final stock. ``storage``, a dict by plant
(bikes), adds a storage capacity at each plant: "M1 with the storage capacities
of the plants", which central_warehouse.md (§6.3) compares with M1 and M2.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .data import F, FORECASTS, K, T, c, c_h, h_0, h_end
from .model import TOL, _constraints, _optimal
from . import figures
from .show import COLOURS, _display, _euros, _european_axes, _light, _number

FORECAST = "Seasonal demand peak"         # M1 is solved with forecast 2
DEMAND = FORECASTS[FORECAST]


def _name(f: str, t: str) -> str:
    return f"{f.replace(' ', '')}_{t}"


def build(demand: dict = DEMAND, months=T, holding: dict = c_h, initial: dict = h_0,
          final: dict | None = h_end, capacity: dict = K, plants=F, storage: dict | None = None):
    """The model of M1, not solved. Returns the model, its variables p, x and h
    (dicts by (f, t)) and the cost expression."""
    model = pulp.LpProblem("plant_stock", pulp.LpMinimize)
    # p[f, t] = bikes assembled, x[f, t] = bikes shipped from plant f in month t
    # (bikes/month); h[f, t] = bikes in stock at plant f at the end of month t (bikes)
    p = {(f, t): model.add_variable(f"p_{_name(f, t)}", lowBound=0) for f in plants for t in months}
    x = {(f, t): model.add_variable(f"x_{_name(f, t)}", lowBound=0) for f in plants for t in months}
    h = {(f, t): model.add_variable(f"h_{_name(f, t)}", lowBound=0) for f in plants for t in months}
    # Minimise the assembly and holding cost
    cost = pulp.lpSum(c[f] * p[f, t] + holding[f] * h[f, t] for f in plants for t in months)
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
            if storage is not None:
                model += (h[f, t] <= storage[f], f"storage_{_name(f, t)}")
        if final is not None:
            model += (h[f, months[-1]] >= final[f], f"final_stock_{f.replace(' ', '')}")
    # The plants together ship at least the demand of each month
    for t in months:
        model += (pulp.lpSum(x[f, t] for f in plants) >= demand[t], f"demand_{t}")
    return model, p, x, h, cost


def solve(demand: dict = DEMAND, months=T, holding: dict = c_h, initial: dict = h_0,
          final: dict | None = h_end, capacity: dict = K, plants=F, storage: dict | None = None) -> dict | None:
    """Solve M1. Returns the cost (EUR), the bikes assembled, shipped and in stock
    of each plant and month (bikes), and the shadow price of the demand of each
    month (EUR/bike); or None if the model has no solution."""
    model, p, x, h, _ = build(demand, months, holding, initial, final, capacity, plants, storage)
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    cons = _constraints(model)
    clean = lambda v: 0.0 if abs(v) < TOL else v      # noqa: E731  (no "-0.0" in tables)
    return {
        "months": list(months),
        "cost": pulp.value(model.objective),
        "assembly": {key: clean(var.value()) for key, var in p.items()},
        "shipments": {key: clean(var.value()) for key, var in x.items()},
        "stock": {key: clean(var.value()) for key, var in h.items()},
        "demand price": {t: clean(cons[f"demand_{t}"].pi) for t in months},
    }


def only_plan(demand: dict = DEMAND, months=T, holding: dict = c_h, initial: dict = h_0,
              final: dict | None = h_end, capacity: dict = K, plants=F,
              storage: dict | None = None) -> bool | None:
    """True if the optimal plan of M1 is the only one: with the cost fixed at its
    optimum, every variable has the same minimum and maximum. False if several
    plans have the optimal cost; None if the model has no solution."""
    model, p, x, h, cost = build(demand, months, holding, initial, final, capacity, plants, storage)
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    model += (cost <= pulp.value(model.objective) + 1e-6, "optimal_cost")
    for var in [*p.values(), *x.values(), *h.values()]:
        ends = []
        for sense in (pulp.LpMinimize, pulp.LpMaximize):
            model.sense = sense
            model.setObjective(var)
            model.solve(pulp.HiGHS(msg=False))
            ends.append(var.value())
        if abs(ends[0] - ends[1]) > 1e-3:          # bikes
            return False
    return True


def _solve(**data) -> tuple[dict | None, bool | None]:
    """Solve M1 with the data given and check whether its plan is the only optimal one."""
    solution = solve(**data)
    return solution, (only_plan(**data) if solution is not None else None)


def why_no_plan(demand: dict = DEMAND, months=T, initial: dict = h_0, final: dict | None = h_end,
                capacity: dict = K, plants=F) -> str:
    """Why M1 has no solution: the first month in which the demand since the start
    of the horizon is above the capacity since the start plus the initial stock,
    or, if there is none, the required final stock that cannot be reached."""
    stock = sum(initial[f] for f in plants)
    demand_so_far = capacity_so_far = 0
    for t in months:
        demand_so_far += demand[t]
        capacity_so_far += sum(capacity[f][t] for f in plants)
        if demand_so_far > capacity_so_far + stock:
            since = f"in {t}" if t == months[0] else f"from {months[0]} to {t}"
            return (f"Unmet demand in {t}: {since} the demand is {_number(demand_so_far)} bikes, and the "
                    f"plants can assemble {_number(capacity_so_far)} and held {_number(stock)} in stock at the "
                    f"start, {_number(demand_so_far - capacity_so_far - stock)} bikes fewer than the demand.")
    if final is not None:
        required = sum(final[f] for f in plants)
        if demand_so_far + required > capacity_so_far + stock:
            return (f"The demand can be met, but not with a required final stock of {_number(required)} bikes "
                    f"at the end of {months[-1]}: the plants can supply "
                    f"{_number(demand_so_far + required - capacity_so_far - stock)} bikes fewer than the demand "
                    f"plus the required final stock.")
    return "The demand and the required final stock of each plant cannot be met together."


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def show_data() -> None:
    """Table 1 and Table 2 of plant_stock.md: the plants and forecast 2; then forecast 2
    against the assembly capacity of the three plants."""
    _display(pd.DataFrame({f: {"Unit assembly cost (€/bike)": c[f],
                               "Capacity (bikes/month, every month)": K[f]["Jan"],
                               "Holding cost (€/(bike·month))": c_h[f],
                               "Initial stock (bikes)": h_0[f],
                               "Required final stock (bikes)": h_end[f]} for f in F})
             .T.rename_axis("Plant"))
    _display(pd.DataFrame({FORECAST: DEMAND}).T.rename_axis("Demand (bikes/month)"))
    figures.orders_figure({"demand": [DEMAND[t] for t in T]}, FORECAST, ylabel="Demand (bikes)",
                          capacity=sum(K[f]["Jan"] for f in F), outline=True)


def _plan_table(solution: dict) -> pd.DataFrame:
    months = solution["months"]
    rows = {}
    for label, key in (("Assembly", "assembly"), ("Shipments", "shipments"),
                       ("Stock at the end of the month", "stock")):
        for f in F:
            rows[label, f] = {t: solution[key][f, t] for t in months}
    return pd.DataFrame(rows).T.rename_axis(["Bikes", "Plant"])


def _by_plant(ax, solution: dict, key: str, label: str, demand: dict, top: float) -> None:
    """Bars stacked by plant, one for each month, with the bikes of each plant
    inside its part of the bar, clear of the point of the demand."""
    months = solution["months"]
    rows = {f: [solution[key][f, t] for t in months] for f in F}
    figures.stacked(ax, months, rows, COLOURS, top=top, totals=False, avoid=[[demand[t]] for t in months])
    for handle in ax.containers:
        handle.set_label(f"{label} {handle.get_label()}")


@_light
def _figure(solution: dict, demand: dict, initial: dict, capacity: dict = K) -> None:
    """Four panels: the assembly of each plant against the capacity of the three
    plants and the demand; the shipments of each plant against the demand; the
    stock of each plant at the end of each month; and the shadow price of the
    demand of each month."""
    months = solution["months"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6))
    x = range(len(months))
    top = max(760, max(demand[t] for t in months) * 1.15)

    ax = axes[0, 0]
    _by_plant(ax, solution, "assembly", "assembly,", demand, top)
    figures.step(ax, months, [sum(capacity[f][t] for f in F) for t in months], color="black", lw=1, ls="--",
                  label="capacity of the three plants")
    ax.plot(x, [demand[t] for t in months], color="black", marker="o", lw=1.2, label="demand")
    ax.set_ylabel("Bikes per month")
    ax.set_title("Assembly of each plant, capacity and demand", fontsize=10)

    ax = axes[0, 1]
    _by_plant(ax, solution, "shipments", "shipments,", demand, top)
    ax.plot(x, [demand[t] for t in months], color="black", marker="o", lw=1.2, label="demand")
    ax.set_ylabel("Bikes per month")
    ax.set_title("Shipments of each plant and demand", fontsize=10)

    # The stock starts from the stock at the end of the month before the horizon
    ax = axes[1, 0]
    start = T[T.index(months[0]) - 1] if months[0] != T[0] else "Dec"
    labels = [start] + months
    rows = {f"stock, {f}": [initial[f]] + [solution["stock"][f, t] for t in months] for f in F}
    totals = [sum(v[i] for v in rows.values()) for i in range(len(labels))]
    figures.stacked(ax, labels, rows, {f"stock, {f}": COLOURS[f] for f in F}, top=max(300, max(totals) * 1.15))
    ax.set_ylabel("Bikes at the end of the month")
    ax.set_title("Stock at the plants at the end of each month", fontsize=10)

    ax = axes[1, 1]
    prices = [solution["demand price"][t] for t in months]
    ax.plot(x, prices, color="black", marker="o", lw=1.2)
    for i, v in enumerate(prices):
        ax.annotate(_number(v), (i, v), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=7.5)
    ax.set_xticks(list(x), months)
    ax.set_xlim(-0.5, len(months) - 0.5)
    ax.set_ylim(0, max(prices) * 1.25 if max(prices) > 0 else 1)
    ax.set_ylabel("€/bike")
    ax.set_title("Shadow price of the demand of each month: the change in the cost\nof the plan with one more bike "
                 "of demand in that month", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    for ax in axes[0]:
        ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, frameon=False)
        ax.spines[["top", "right"]].set_visible(False)
    axes[1, 0].legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=3, frameon=False)
    _european_axes(fig)
    fig.tight_layout()
    plt.show()


def _report(solution: dict | None, demand: dict, initial: dict, heading: str,
            unique: bool | None = True, show_tables: bool = False) -> None:
    """The cost of the plan and whether other plans have the same cost; then the
    plan and the shadow prices of the demand in the figure or, with
    ``show_tables``, in tables."""
    if solution is None:
        print(f"{heading}: the model has no solution.")
        return
    months = solution["months"]
    print(f"{heading}: optimal plan, cost {_euros(solution['cost'])}.")
    if not unique:
        print("With these data the model has several optimal plans with the same cost; "
              "the cell shows one of them.")
    if show_tables:
        _display(_plan_table(solution))
        print("Shadow price of the demand of each month (€/bike): the change in the cost of the plan with one more "
              "bike of demand in that month.")
        _display(pd.DataFrame({t: {"Shadow price (€/bike)": solution["demand price"][t]} for t in months}))
    else:
        _figure(solution, demand, initial)


def stock_plan(with_required_final_stock: bool = True, show_tables: bool = False) -> dict | None:
    """The plan with forecast 2, with or without the required final stock."""
    final = h_end if with_required_final_stock else None
    heading = f"{FORECAST}, {'with' if with_required_final_stock else 'without'} the required final stock"
    solution, unique = _solve(final=final)
    _report(solution, DEMAND, h_0, heading, unique, show_tables)
    return solution


def holding_cost_test(holding_plant_1: float = 5, show_tables: bool = False) -> dict | None:
    """The plan with the three holding costs moved together: plant 2 costs 1 €/(bike·month)
    more than plant 1, and plant 3 costs 2 more."""
    holding = {"Plant 1": holding_plant_1, "Plant 2": holding_plant_1 + 1, "Plant 3": holding_plant_1 + 2}
    print("Holding cost (€/(bike·month)): "
          + "; ".join(f"{f.lower()} {_number(v)}" for f, v in holding.items()) + ".")
    solution, unique = _solve(holding=holding)
    if solution is not None:
        march = sum(solution["stock"][f, "Mar"] for f in F)
        plant_3 = {t: solution["assembly"]["Plant 3", t] for t in T if solution["assembly"]["Plant 3", t] > TOL}
        print(f"Seasonal stock at the end of March: {_number(march)} bikes. Bikes assembled at plant 3: "
              + ("; ".join(f"{_number(v)} in {t}" for t, v in plant_3.items()) if plant_3 else "none") + ".")
    _report(solution, DEMAND, h_0, f"{FORECAST}, with the required final stock", unique, show_tables)
    return solution


def demand_test(month: str = "Apr", demand: float = 650, show_tables: bool = False) -> dict | None:
    """The plan with the demand of one month changed, the rest of forecast 2 unchanged;
    if there is no solution, the month in which capacity falls short."""
    if month not in T:
        raise ValueError(f"The month must be one of {', '.join(T)}.")
    changed = dict(DEMAND, **{month: demand})
    print("Demand (bikes/month): " + "; ".join(f"{t} {_number(changed[t])}" for t in T) + ".")
    solution, unique = _solve(demand=changed)
    _report(solution, changed, h_0, f"Demand of {month} {_number(demand)}, with the required final stock",
            unique, show_tables)
    if solution is None:
        print(why_no_plan(demand=changed))
    return solution


def horizon_test(last_month: str = "Mar", show_tables: bool = False) -> tuple[dict | None, dict | None]:
    """A plan from January to the last month, with the required final stock at the
    end of that month; then, from the stock it leaves, a plan for the months left until June."""
    if last_month not in T:
        raise ValueError(f"The last month must be one of {', '.join(T)}.")
    i = T.index(last_month)
    first_months, later_months = T[:i + 1], T[i + 1:]
    first, unique = _solve(months=first_months)
    _report(first, DEMAND, h_0, f"Plan from {first_months[0]} to {last_month}", unique, show_tables)
    if first is None:
        print(why_no_plan(months=first_months))
        return None, None
    if not later_months:
        return first, None
    left = {f: first["stock"][f, last_month] for f in F}
    print(f"Stock at the end of {last_month} (bikes): "
          + "; ".join(f"{f.lower()} {_number(v)}" for f, v in left.items()) + ".")
    print()
    later, unique = _solve(months=later_months, initial=left)
    _report(later, DEMAND, left,
            f"Plan from {later_months[0]} to {later_months[-1]}, from that stock", unique, show_tables)
    if later is None:
        print(why_no_plan(months=later_months, initial=left))
    return first, later


def final_stock_test(plant: str = "Plant 1", required_final_stock: float = 20,
                     show_tables: bool = False) -> dict | None:
    """The plan with the required final stock of one plant changed; the other plants
    keep theirs."""
    if plant not in F:
        raise ValueError(f"The plant must be one of {', '.join(F)}.")
    final = dict(h_end, **{plant: required_final_stock})
    print("Required final stock (bikes): "
          + "; ".join(f"{f.lower()} {_number(v)}" for f, v in final.items()) + ".")
    solution, unique = _solve(final=final)
    _report(solution, DEMAND, h_0, f"{FORECAST}, with that required final stock", unique, show_tables)
    if solution is None:
        print(why_no_plan(final=final))
    return solution
