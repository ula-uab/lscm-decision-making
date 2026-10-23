"""M1 · Stock at the plants (plant_stock.md): the model of production_plan.md (M0)
with stock at each plant from one month to the next, written with PuLP and solved
with HiGHS, and what the notebook plant_stock.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the plants with their costs, capacities and stocks, and forecast 2;
2. ``stock_plan``: the plan with forecast 2, with or without the required ending stock;
3. ``holding_cost_test``, ``demand_test``, ``horizon_test`` and ``ending_stock_test``:
   the plan when one datum changes.

A capacity is given as capacity[f][t] (bikes/month), a demand as demand[t]
(bikes/month), and holding costs and stocks as dicts by plant. ``final=None``
solves the model without the required ending stock.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .data import F, FORECASTS, K, T, c, c_h, h_0, h_end
from .model import TOL, _constraints, _optimal
from .show import COLOURS, _display, _euros, _light

FORECAST = "Forecast 2"                   # M1 is solved with forecast 2
DEMAND = FORECASTS[FORECAST]


def _name(f: str, t: str) -> str:
    return f"{f.replace(' ', '')}_{t}"


def build(demand: dict = DEMAND, months=T, holding: dict = c_h, initial: dict = h_0,
          final: dict | None = h_end, capacity: dict = K, plants=F):
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
        if final is not None:
            model += (h[f, months[-1]] >= final[f], f"final_stock_{f.replace(' ', '')}")
    # The plants together ship at least the demand of each month
    for t in months:
        model += (pulp.lpSum(x[f, t] for f in plants) >= demand[t], f"demand_{t}")
    return model, p, x, h, cost


def solve(demand: dict = DEMAND, months=T, holding: dict = c_h, initial: dict = h_0,
          final: dict | None = h_end, capacity: dict = K, plants=F) -> dict | None:
    """Solve M1. Returns the cost (EUR), the bikes assembled, shipped and in stock
    of each plant and month (bikes), and the shadow price of the demand of each
    month (EUR/bike); or None if the model has no solution."""
    model, p, x, h, _ = build(demand, months, holding, initial, final, capacity, plants)
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
              final: dict | None = h_end, capacity: dict = K, plants=F) -> bool | None:
    """True if the optimal plan of M1 is the only one: with the cost fixed at its
    optimum, every variable has the same minimum and maximum. False if several
    plans have the optimal cost; None if the model has no solution."""
    model, p, x, h, cost = build(demand, months, holding, initial, final, capacity, plants)
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
    or, if there is none, the required ending stock that cannot be reached."""
    stock = sum(initial[f] for f in plants)
    demand_so_far = capacity_so_far = 0
    for t in months:
        demand_so_far += demand[t]
        capacity_so_far += sum(capacity[f][t] for f in plants)
        if demand_so_far > capacity_so_far + stock:
            since = f"in {t}" if t == months[0] else f"from {months[0]} to {t}"
            return (f"Unmet demand in {t}: {since} the demand is {demand_so_far:,.0f} bikes, and the "
                    f"plants can assemble {capacity_so_far:,.0f} and held {stock:,.0f} in stock at the "
                    f"start, {demand_so_far - capacity_so_far - stock:,.0f} bikes fewer than the demand.")
    if final is not None:
        required = sum(final[f] for f in plants)
        if demand_so_far + required > capacity_so_far + stock:
            return (f"The demand can be met, but not with a required ending stock of {required:,.0f} bikes "
                    f"at the end of {months[-1]}: the plants can supply "
                    f"{demand_so_far + required - capacity_so_far - stock:,.0f} bikes fewer than the demand "
                    f"plus the required ending stock.")
    return "The demand and the required ending stock of each plant cannot be met together."


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def show_data() -> None:
    """Table 1 and Table 2 of plant_stock.md: the plants and forecast 2."""
    _display(pd.DataFrame({f: {"Unit assembly cost (€/bike)": c[f],
                               "Capacity (bikes/month, every month)": K[f]["Jan"],
                               "Holding cost (€/(bike·month))": c_h[f],
                               "Stock at the end of December (bikes)": h_0[f],
                               "Required ending stock (bikes)": h_end[f]} for f in F})
             .T.rename_axis("Plant"))
    _display(pd.DataFrame({FORECAST: DEMAND}).T.rename_axis("Demand (bikes/month)"))


def _plan_table(solution: dict) -> pd.DataFrame:
    months = solution["months"]
    rows = {}
    for label, key in (("Assembled", "assembly"), ("Shipped", "shipments"),
                       ("Stock at the end of the month", "stock")):
        for f in F:
            rows[label, f] = {t: solution[key][f, t] for t in months}
    return pd.DataFrame(rows).T.rename_axis(["Bikes", "Plant"])


@_light
def _figure(solution: dict, demand: dict, initial: dict, capacity: dict = K) -> None:
    """Left: bikes assembled by each plant, with the capacity of the three plants
    and the demand. Right: bikes in stock at each plant at the end of each month."""
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
    left.plot(x, [demand[t] for t in months], color="black", marker="o", label="demand")
    left.set_xticks(list(x), months)
    left.set_ylabel("Bikes/month")
    left.set_ylim(0, max(760, max(demand[t] for t in months) * 1.1))
    left.set_title("Bikes assembled, capacity and demand", fontsize=10)
    left.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False)
    left.spines[["top", "right"]].set_visible(False)

    # The stock starts from the stock at the end of the month before the horizon
    start = T[T.index(months[0]) - 1] if months[0] != T[0] else "Dec"
    labels = [start] + months
    bottom = [0.0] * len(labels)
    for f in F:
        values = [initial[f]] + [solution["stock"][f, t] for t in months]
        right.bar(range(len(labels)), values, bottom=bottom, color=COLOURS[f], width=0.7, label=f"stock {f}")
        bottom = [b + v for b, v in zip(bottom, values)]
    right.set_xticks(range(len(labels)), labels)
    right.set_ylabel("Bikes at the end of the month")
    right.set_ylim(0, max(300, max(bottom) * 1.15))
    right.set_title("Stock at the plants", fontsize=10)
    right.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False)
    right.spines[["top", "right"]].set_visible(False)
    plt.show()


def _report(solution: dict | None, demand: dict, initial: dict, heading: str,
            unique: bool | None = True) -> None:
    """The plan and its cost, whether other plans have the same cost, the shadow
    prices of the demand and the figure."""
    if solution is None:
        print(f"{heading}: the model has no solution.")
        return
    months = solution["months"]
    print(f"{heading}: optimal plan, cost {_euros(solution['cost'])}.")
    _display(_plan_table(solution))
    if not unique:
        print("With these data the model has several optimal plans with the same cost; "
              "the table shows one of them.")
    print("Shadow price of the demand of each month (€/bike): what one more bike of demand costs.")
    _display(pd.DataFrame({t: {"Shadow price (€/bike)": solution["demand price"][t]} for t in months}))
    _figure(solution, demand, initial)


def stock_plan(with_required_ending_stock: bool = True) -> dict | None:
    """The plan with forecast 2, with or without the required ending stock."""
    final = h_end if with_required_ending_stock else None
    heading = f"{FORECAST}, {'with' if with_required_ending_stock else 'without'} the required ending stock"
    solution, unique = _solve(final=final)
    _report(solution, DEMAND, h_0, heading, unique)
    return solution


def holding_cost_test(holding_plant_1: float = 5) -> dict | None:
    """The plan with the three holding costs moved together: plant 2 costs 1 €/(bike·month)
    more than plant 1, and plant 3 costs 2 more."""
    holding = {"Plant 1": holding_plant_1, "Plant 2": holding_plant_1 + 1, "Plant 3": holding_plant_1 + 2}
    print("Holding cost (€/(bike·month)): " + ", ".join(f"{f.lower()} {v:g}" for f, v in holding.items()) + ".")
    solution, unique = _solve(holding=holding)
    if solution is not None:
        march = sum(solution["stock"][f, "Mar"] for f in F)
        plant_3 = {t: solution["assembly"]["Plant 3", t] for t in T if solution["assembly"]["Plant 3", t] > TOL}
        print(f"Seasonal stock at the end of March: {march:,.0f} bikes. Bikes assembled at plant 3: "
              + (", ".join(f"{v:,.0f} in {t}" for t, v in plant_3.items()) if plant_3 else "none") + ".")
    _report(solution, DEMAND, h_0, f"{FORECAST}, with the required ending stock", unique)
    return solution


def demand_test(month: str = "Apr", demand: float = 650) -> dict | None:
    """The plan with the demand of one month changed, the rest of forecast 2 unchanged;
    if there is no solution, the month in which capacity falls short."""
    if month not in T:
        raise ValueError(f"The month must be one of {', '.join(T)}.")
    changed = dict(DEMAND, **{month: demand})
    print("Demand (bikes/month): " + ", ".join(f"{t} {changed[t]:g}" for t in T) + ".")
    solution, unique = _solve(demand=changed)
    _report(solution, changed, h_0, f"Demand of {month} {demand:g}, with the required ending stock", unique)
    if solution is None:
        print(why_no_plan(demand=changed))
    return solution


def horizon_test(last_month: str = "Mar") -> tuple[dict | None, dict | None]:
    """A plan from January to the last month, with the required ending stock at the
    end of that month; then, from the stock it leaves, a plan for the months left until June."""
    if last_month not in T:
        raise ValueError(f"The last month must be one of {', '.join(T)}.")
    i = T.index(last_month)
    first_months, later_months = T[:i + 1], T[i + 1:]
    first, unique = _solve(months=first_months)
    _report(first, DEMAND, h_0, f"Plan from {first_months[0]} to {last_month}", unique)
    if first is None:
        print(why_no_plan(months=first_months))
        return None, None
    if not later_months:
        return first, None
    left = {f: first["stock"][f, last_month] for f in F}
    print(f"Stock at the end of {last_month} (bikes): "
          + ", ".join(f"{f.lower()} {v:g}" for f, v in left.items()) + ".")
    print()
    later, unique = _solve(months=later_months, initial=left)
    _report(later, DEMAND, left,
            f"Plan from {later_months[0]} to {later_months[-1]}, from that stock", unique)
    if later is None:
        print(why_no_plan(months=later_months, initial=left))
    return first, later


def ending_stock_test(plant: str = "Plant 1", required_ending_stock: float = 20) -> dict | None:
    """The plan with the required ending stock of one plant changed; the other plants
    keep theirs."""
    if plant not in F:
        raise ValueError(f"The plant must be one of {', '.join(F)}.")
    final = dict(h_end, **{plant: required_ending_stock})
    print("Required ending stock (bikes): "
          + ", ".join(f"{f.lower()} {v:g}" for f, v in final.items()) + ".")
    solution, unique = _solve(final=final)
    _report(solution, DEMAND, h_0, f"{FORECAST}, with that required ending stock", unique)
    if solution is None:
        print(why_no_plan(final=final))
    return solution
