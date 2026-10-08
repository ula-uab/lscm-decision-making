"""What the notebook shows: tables, figures and short messages.

Each function answers one step of the notebook, so that its cells only need
one line of code.
"""

from __future__ import annotations

import functools

import matplotlib.pyplot as plt
import pandas as pd

from . import model as m
from .data import FORECASTS, K, REDUCED_F, T, F, c

COLOURS = {"Plant 1": "tab:blue", "Plant 2": "tab:orange", "Plant 3": "tab:purple"}
SHORT = "tab:red"
BEST = "tab:green"


def _light(func):
    """Draw with matplotlib's default style: white background and dark text, also
    when the editor has a dark theme."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with plt.style.context("default"):
            return func(*args, **kwargs)
    return wrapper


def _display(obj) -> None:
    try:
        from IPython.display import display
        display(obj)
    except ImportError:
        print(obj)


def _euros(x: float) -> str:
    return f"{x:,.0f} €"


def _forecast(name: str) -> dict:
    if name not in FORECASTS:
        raise ValueError(f"The forecast must be one of {', '.join(FORECASTS)}.")
    return FORECASTS[name]


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def show_data() -> None:
    """Tables 1 and 2: the plants and the two demand forecasts."""
    _display(pd.DataFrame({f: {"Unit assembly cost (€/bike)": c[f],
                               "Capacity (bikes/month, every month)": K[f]["Jan"]} for f in F})
             .T.rename_axis("Plant"))
    _display(pd.DataFrame(FORECASTS).T.rename_axis("Demand (bikes/month)"))


# ---------------------------------------------------------------------------
# §3 Reduced version: two plants, one month
# ---------------------------------------------------------------------------

def _range_text(low, high) -> str:
    low_text = "no lower limit" if low is None else f"{low:g}"
    high_text = "no upper limit" if high is None else f"{high:g}"
    return f"{low_text} to {high_text}"


@_light
def feasible_region(k1: float = 250, demand: float = 380) -> None:
    """The feasible region of the reduced version, its vertices, the lines of equal
    cost and the optimum; then the shadow prices and the ranges in which they hold."""
    k2 = K["Plant 2"]["Jan"]
    corners = m.vertices(k1, k2, demand)
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    top = max(k1, k2, demand) * 1.15 + 20
    # Constraint lines
    ax.plot([k1, k1], [0, top], color=COLOURS["Plant 1"], lw=1.5, label=f"capacity of plant 1: p1 ≤ {k1:g}")
    ax.plot([0, top], [k2, k2], color=COLOURS["Plant 2"], lw=1.5, label=f"capacity of plant 2: p2 ≤ {k2:g}")
    ax.plot([0, demand], [demand, 0], color="black", lw=1.5, label=f"demand: p1 + p2 ≥ {demand:g}")
    ax.set_xlim(0, top)
    ax.set_ylim(0, top)
    ax.set_xlabel("p1: bikes assembled in plant 1 (bikes/month)")
    ax.set_ylabel("p2: bikes assembled in plant 2 (bikes/month)")
    ax.spines[["top", "right"]].set_visible(False)
    if not corners:
        ax.legend(fontsize=8, loc="upper right")
        plt.show()
        print(f"No plan: the two plants can assemble at most {k1 + k2:g} bikes, "
              f"and the demand is {demand:g}. The feasible region is empty.")
        return
    # Feasible region, its vertices and lines of equal cost through each vertex
    centre = (sum(x for x, _ in corners) / len(corners), sum(y for _, y in corners) / len(corners))
    import math
    ordered = sorted(corners, key=lambda v: math.atan2(v[1] - centre[1], v[0] - centre[0]))
    ax.fill(*zip(*ordered), color="tab:green", alpha=0.15, label="feasible region")
    solution = m.reduced(k1, demand)
    best = (solution["plan"][("Plant 1", "Jan")], solution["plan"][("Plant 2", "Jan")])
    for v in corners:
        z = m.reduced_cost_of(v)
        xs = [0, top]
        ys = [(z - c["Plant 1"] * x) / c["Plant 2"] for x in xs]
        ax.plot(xs, ys, color="0.6", ls=":", lw=1)
        is_best = abs(v[0] - best[0]) < 1e-6 and abs(v[1] - best[1]) < 1e-6
        ax.scatter(*v, s=90 if is_best else 40, color=BEST if is_best else "black", zorder=3)
        ax.annotate(f"({v[0]:g}, {v[1]:g})\n{_euros(z)}", v, xytext=(8, 4), textcoords="offset points",
                    fontsize=8, weight="bold" if is_best else "normal")
    ax.plot([], [], color="0.6", ls=":", label="equal cost: 310 p1 + 340 p2 = constant")
    ax.legend(fontsize=8, loc="upper right")
    plt.show()

    _display(pd.DataFrame([{"p1 (bikes)": v[0], "p2 (bikes)": v[1], "Cost (€)": m.reduced_cost_of(v)}
                           for v in corners]).rename_axis("Vertex"))
    print(f"Optimum: p1 = {best[0]:g}, p2 = {best[1]:g}, cost {_euros(solution['cost'])}.")
    print()
    capacity = {f: dict(K[f]) for f in REDUCED_F}
    capacity["Plant 1"]["Jan"] = k1
    rows = []
    for kind, key, name, rhs in (("capacity", ("Plant 1", "Jan"), "Capacity of plant 1", k1),
                                 ("capacity", ("Plant 2", "Jan"), "Capacity of plant 2", k2),
                                 ("demand", "Jan", "Demand", demand)):
        price = (solution["capacity price"][key] if kind == "capacity" else solution["demand price"][key])
        low, high = m.validity_range(kind, key, REDUCED_F, ["Jan"], {"Jan": demand}, capacity)
        rows.append({"Constraint": name, "Right-hand side (bikes)": rhs, "Shadow price (€/bike)": price,
                     "Holds from … to … (bikes)": _range_text(low, high)})
    _display(pd.DataFrame(rows).set_index("Constraint"))


# ---------------------------------------------------------------------------
# §4 and §5 The full case
# ---------------------------------------------------------------------------

def _plan_table(solution: dict) -> pd.DataFrame:
    table = pd.DataFrame({t: {f: solution["plan"][f, t] for f in F} for t in T})
    table.loc["Total"] = table.sum()
    return table.rename_axis("Bikes assembled")


def production_plan(forecast: str = "Forecast 1") -> dict | None:
    """The optimal plan for a forecast, its cost, the shadow prices of the demand and
    the reduced costs; or, if the model has no solution, the months that cannot be served."""
    demand = _forecast(forecast)
    solution = m.solve(demand=demand)
    if solution is None:
        short = m.shortfall(demand)
        print(f"{forecast}: the model has no solution. The total capacity is "
              f"{m.monthly_capacity()['Jan']} bikes/month and the demand is above it in "
              + ", ".join(f"{t} (by {v} bikes)" for t, v in short.items()) + ".")
        print("The next cell compares capacity and demand month by month.")
        return None
    print(f"{forecast}: optimal plan, cost {_euros(solution['cost'])}.")
    _display(_plan_table(solution))
    print("Shadow price of the demand of each month (€/bike): what one more bike of demand costs.")
    _display(pd.DataFrame({t: {"Shadow price (€/bike)": solution["demand price"][t]} for t in T}))
    print("Reduced cost of each plant and month (€/bike): how much cheaper the plant would have to be "
          "to assemble bikes that month. Zero where the plant is used.")
    _display(pd.DataFrame({t: {f: solution["reduced cost"][f, t] for f in F} for t in T})
             .rename_axis("Reduced cost"))
    print("Shadow price of each capacity (€/bike): what one more bike of capacity saves (negative: a saving).")
    _display(pd.DataFrame({t: {f: solution["capacity price"][f, t] for f in F} for t in T})
             .rename_axis("Capacity shadow price"))
    return solution


@_light
def capacity_and_demand(forecast: str = "Forecast 2") -> None:
    """Total capacity and demand month by month, with the months where capacity
    falls short; and the cumulative demand against the cumulative capacity."""
    demand = _forecast(forecast)
    rows = m.cumulative(demand)
    fig, (left, right) = plt.subplots(1, 2, figsize=(11, 3.8))
    x = range(len(T))
    bottom = [0] * len(T)
    for f in F:
        values = [K[f][t] for t in T]
        left.bar(x, values, bottom=bottom, color=COLOURS[f], alpha=0.35, width=0.7, label=f"capacity {f}")
        bottom = [b + v for b, v in zip(bottom, values)]
    left.plot(x, [demand[t] for t in T], marker="o", color="black", label="demand")
    short = m.shortfall(demand)
    for i, t in enumerate(T):
        if t in short:
            left.annotate(f"{short[t]} short", (i, demand[t]), xytext=(0, 8), textcoords="offset points",
                          ha="center", color=SHORT, weight="bold", fontsize=8)
            left.scatter([i], [demand[t]], s=120, facecolor="none", edgecolor=SHORT, lw=2, zorder=3)
    left.set_xticks(list(x), T)
    left.set_ylabel("Bikes/month")
    left.set_ylim(0, 760)
    left.set_title(f"{forecast}: capacity and demand each month", fontsize=10)
    left.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=4, frameon=False)
    left.spines[["top", "right"]].set_visible(False)

    right.plot(x, [r["cumulative capacity"] for r in rows], marker="s", label="cumulative capacity")
    right.plot(x, [r["cumulative demand"] for r in rows], marker="o", color="black", label="cumulative demand")
    right.set_xticks(list(x), T)
    right.set_ylabel("Bikes since January")
    right.set_title("Cumulative capacity and demand", fontsize=10)
    right.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
    right.spines[["top", "right"]].set_visible(False)
    plt.show()

    _display(pd.DataFrame(rows).set_index("month").rename_axis("Month")
             .rename(columns={"demand": "Demand", "capacity": "Capacity", "spare": "Spare capacity",
                              "cumulative demand": "Cumulative demand",
                              "cumulative capacity": "Cumulative capacity"}).T)
    if short:
        never = all(r["cumulative capacity"] >= r["cumulative demand"] for r in rows)
        print("Capacity falls short in " + ", ".join(f"{t} ({v} bikes)" for t, v in short.items()) + ".")
        if never:
            print("The cumulative capacity is never below the cumulative demand: a plan that keeps "
                  "bikes in stock from one month to the next would exist. The model has no such plan "
                  "because it does not represent stock.")
    else:
        print("The capacity covers the demand every month.")
