"""What the notebook shows: tables, figures and short messages.

Each function answers one step of the notebook, so that its cells only need
one line of code.
"""

from __future__ import annotations

import functools

import matplotlib.pyplot as plt
import pandas as pd

from . import forecast as fc
from . import model as m
from .data import POSITIONS, C, K, W, d, k, order_C3_week13, orders_C3, t

COLOURS = {"W1": "tab:blue", "W2": "tab:orange"}
OVER = "tab:red"

SECONDS_PER_YEAR = 365.25 * 24 * 3600
AGE_OF_UNIVERSE_YEARS = 13.8e9      # Planck Collaboration (2020), A&A 641, A6
PLANS_PER_SECOND = 1e9              # assumed: a computer that checks a billion plans per second


def _light(func):
    """Draw with matplotlib's default style: white background and dark text, also
    when the editor has a dark theme (PyCharm changes the colours of the text)."""
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


def _pallets(x: float) -> str:
    return f"{x:g} pallet" + ("" if x == 1 else "s")


def _euros(x: float) -> str:
    return f"{x:,.0f} €"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

def data_tables() -> None:
    """Tables 1-4: capacity, demand, shipping cost and delivery time."""
    capacity = pd.DataFrame({"Capacity (pallets/week)": K}).rename_axis("Warehouse")
    demand = pd.DataFrame({"Forecast demand (pallets/week)": d}).rename_axis("Customer")
    demand.loc["Total"] = sum(d.values())
    cost = pd.DataFrame(k).T.rename_axis("Shipping cost (€/pallet)")
    time = pd.DataFrame(t).T.rename_axis("Delivery time (days)")
    for table in (capacity, demand, cost, time):
        _display(table)


def plan_table(plans: dict[str, dict], demand: dict = d) -> pd.DataFrame:
    """One row per plan: warehouse of each customer, loads, cost and delivery time."""
    rows = {}
    for name, plan in plans.items():
        load = m.loads(plan, demand)
        row = {c: plan[c] for c in C}
        row.update({f"Load {w}": load[w] for w in W})
        row["Feasible"] = "yes" if m.is_feasible(plan, demand=demand) else (
            "no (" + ", ".join(m.excess(plan, demand=demand)) + ")")
        row["Cost (€/week)"] = m.cost(plan, demand)
        row["Average delivery time (days)"] = f"{m.average_delivery_time(plan):.2f}"
        rows[name] = row
    return pd.DataFrame(rows).T.rename_axis("Plan")


def all_plans_table() -> pd.DataFrame:
    """Table 6: the 16 plans, feasible ones first, each group ordered by cost."""
    plans = sorted(m.all_plans(), key=lambda p: (not m.is_feasible(p), m.cost(p)))
    named = {}
    for i, plan in enumerate(plans, start=1):
        named[m.name_of(plan) or f"#{i}"] = plan
    return plan_table(named)


def _readable_time(seconds: float) -> str:
    if seconds < 1:
        return "less than a second"
    if seconds < 3600:
        return f"{seconds:,.0f} seconds"
    if seconds < SECONDS_PER_YEAR:
        return f"{seconds / 86400:,.1f} days"
    years = seconds / SECONDS_PER_YEAR
    return f"{years:,.0f} years" if years < 1e6 else f"{years:.1e} years"


def explosion_table(sizes=((2, 4), (3, 10), (5, 30), (10, 50), (10, 200))) -> pd.DataFrame:
    """How the number of plans m^n grows, and how long checking them all would take."""
    rows = []
    for n_warehouses, n_customers in sizes:
        plans = n_warehouses ** n_customers
        seconds = plans / PLANS_PER_SECOND
        years = seconds / SECONDS_PER_YEAR
        rows.append({
            "Warehouses": n_warehouses,
            "Customers": n_customers,
            "Plans": f"{plans:,}" if plans < 10 ** 12 else f"a number with {len(str(plans))} digits",
            "Time to check them all": _readable_time(seconds),
            "Times the age of the universe": (f"{years / AGE_OF_UNIVERSE_YEARS:.1e}"
                                              if years > AGE_OF_UNIVERSE_YEARS else "—"),
        })
    return pd.DataFrame(rows).set_index(["Warehouses", "Customers"])


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------

@_light
def plot_map(plan: dict | None = None, ax=None, title: str = "", demand: dict = d):
    """Schematic map (not to scale). With a plan, each customer is joined to its warehouse.

    Squares are warehouses (capacity) and circles customers (demand), in pallets/week."""
    ax = ax or plt.subplots(figsize=(7, 4))[1]
    for c in C:
        for w in W:
            (x0, y0), (x1, y1) = POSITIONS[w], POSITIONS[c]
            # Labels near the customer end, so that crossing links do not share a label
            share = 0.68 if plan is None else 0.5
            lx, ly = x0 + share * (x1 - x0), y0 + share * (y1 - y0)
            if plan is None:
                ax.plot([x0, x1], [y0, y1], color="0.75", lw=1, ls="--", zorder=1)
                ax.text(lx, ly, f"{k[w][c]} € · {t[w][c]} d", fontsize=7, color="0.25",
                        ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.6),
                        zorder=2)
            elif plan[c] == w:
                ax.plot([x0, x1], [y0, y1], color=COLOURS[w], lw=1 + demand[c] / 10, zorder=1)
                ax.text(lx, ly, f"{k[w][c]} €/pallet", fontsize=7, ha="center", va="center",
                        bbox=dict(fc="white", ec="none", pad=0.6), zorder=2)
    for w in W:
        x, y = POSITIONS[w]
        ax.scatter(x, y, s=1700, marker="s", color=COLOURS[w], zorder=3)
        ax.text(x, y, f"{w}\n≤ {K[w]}", color="white", weight="bold", fontsize=8,
                ha="center", va="center", zorder=4)
    for c in C:
        x, y = POSITIONS[c]
        colour = COLOURS[plan[c]] if plan else "0.4"
        ax.scatter(x, y, s=1100, color="white", edgecolor=colour, lw=2, zorder=3)
        ax.text(x, y, f"{c}\n{demand[c]:g}", ha="center", va="center", fontsize=8, zorder=4)
    ax.set_xlim(-0.6, 10.6)
    ax.set_ylim(-0.4, 5.4)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title or ("Cost per pallet and delivery time of each link" if plan is None else
                           "Who serves whom"), fontsize=10)
    if plan is None:
        ax.text(5, -0.4, "Squares: warehouses and their capacity · circles: customers and their demand "
                "(pallets/week) · not to scale", fontsize=7, color="0.4", ha="center", va="top")
    return ax


@_light
def plot_loads(plan: dict, capacity: dict = K, demand: dict = d, ax=None, title: str = ""):
    """Pallets shipped by each warehouse, stacked by customer, against its capacity."""
    ax = ax or plt.subplots(figsize=(4, 3.6))[1]
    for i, w in enumerate(W):
        bottom = 0
        for c in C:
            if plan[c] != w:
                continue
            ax.bar(i, demand[c], bottom=bottom, color=COLOURS[w], edgecolor="white", width=0.6)
            ax.text(i, bottom + demand[c] / 2, f"{c}\n{demand[c]:g}", color="white",
                    ha="center", va="center", fontsize=8)
            bottom += demand[c]
        over = bottom > capacity[w]
        ax.hlines(capacity[w], i - 0.42, i + 0.42, color="black", lw=2,
                  label="capacity" if i == 0 else None)
        if over:
            ax.bar(i, bottom - capacity[w], bottom=capacity[w], width=0.6, color="none",
                   edgecolor=OVER, hatch="///", lw=2)
            ax.text(i, max(bottom, capacity[w]) + 5, f"{bottom - capacity[w]:g} too many", color=OVER,
                    ha="center", va="bottom", fontsize=9, weight="bold")
    ax.set_xticks(range(len(W)), W)
    ax.set_xlim(-0.6, len(W) - 0.4)
    ax.legend(fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
    ax.set_ylim(0, max(sum(demand.values()), max(capacity.values())) + 20)
    ax.set_ylabel("Pallets/week")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(title, fontsize=10)
    return ax


@_light
def show_data() -> None:
    """Tables 1-4 and the map of the example."""
    data_tables()
    plot_map()
    plt.show()


# ---------------------------------------------------------------------------
# Steps of the notebook
# ---------------------------------------------------------------------------

def _summary(plan: dict, capacity: dict = K, demand: dict = d) -> None:
    load = m.loads(plan, demand)
    for w in W:
        status = "over capacity" if load[w] > capacity[w] else f"{capacity[w] - load[w]:g} spare"
        print(f"  {w} ships {load[w]:g} of {capacity[w]:g} pallets ({status})")
    print(f"  Cost: {_euros(m.cost(plan, demand))}/week")
    if demand is d:
        print(f"  Average delivery time: {m.average_delivery_time(plan):.2f} days")


@_light
def check_plan(plan: dict, title: str = "Your plan", capacity: dict = K,
               demand: dict = d) -> bool:
    """Draw a plan on the map with its warehouse loads, and say whether it is feasible."""
    plan = m.check(plan)
    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 3.8),
                                      gridspec_kw={"width_ratios": [1.6, 1]})
    plot_map(plan, ax=left, demand=demand)
    plot_loads(plan, capacity, demand, ax=right)
    fig.suptitle(title, fontsize=12)
    plt.show()
    feasible = m.is_feasible(plan, capacity, demand)
    name = m.name_of(plan)
    print(title)
    if name and f"plan {name}" not in title:
        print(f"  This is plan {name} of Table 6.")
    _summary(plan, capacity, demand)
    if feasible:
        print("  Feasible: every warehouse is within its capacity.")
    else:
        too_many = ", ".join(f"{w} by {_pallets(e)}" for w, e in m.excess(plan, capacity, demand).items())
        print(f"  Not feasible: over capacity in {too_many}.")
    return feasible


def rule_of_thumb() -> None:
    """§3: nearest warehouse (not feasible), then diverted by hand (plan M)."""
    check_plan(m.nearest_warehouse_plan(), "Rule of thumb: each customer from its nearest warehouse")
    print()
    check_plan(m.diverted_by_hand_plan(), "Diverted by hand: plan M")


def challenge(plan: dict) -> None:
    """Check a plan that tries to beat plan M."""
    plan = m.check(plan)
    feasible = check_plan(plan, "Your plan against plan M")
    target = m.cost(m.diverted_by_hand_plan())
    mine = m.cost(plan)
    print()
    if not feasible:
        print("A plan that does not fit in the warehouses cannot be used. Try again.")
    elif mine < target:
        print(f"Well done: your plan costs {_euros(target - mine)}/week less than plan M.")
        print("Is it the cheapest of all? The model will tell, in the next step.")
    else:
        print(f"Plan M costs {_euros(target)}/week; yours costs {_euros(mine)}. Not better yet.")
        print("Hint: plan M diverts C3 because it happens to come last. Diverting a customer to W2")
        print("costs (cost from W2 - cost from W1) x pallets. Which customer is cheapest to divert?")


def solve_model() -> dict:
    """§3: the plan of the model (plan A) against plan M (Table 5)."""
    plan_a = m.solve()
    plan_m = m.diverted_by_hand_plan()
    _display(plan_table({"M · diverted by hand": plan_m, "A · model": plan_a}))
    saving = m.cost(plan_m) - m.cost(plan_a)
    print(f"The model saves {_euros(saving)}/week "
          f"({100 * saving / m.cost(plan_m):.0f} % of the cost of plan M).")
    for c in ("C3", "C2"):
        extra = k["W2"][c] - k["W1"][c]
        print(f"  Diverting {c} to W2 costs {extra} € more per pallet on {d[c]} pallets: "
              f"{_euros(extra * d[c])}/week.")
    check_plan(plan_a, "The plan of the model: plan A")
    return plan_a


def compare_methods() -> None:
    """§4: checking all 16 plans and the solver give the same plan."""
    brute = m.best_by_brute_force()
    solver = m.solve()
    print(f"Checking all 16 plans: plan {m.name_of(brute)}, {_euros(m.cost(brute))}/week")
    print(f"Solver (PuLP + HiGHS): plan {m.name_of(solver)}, {_euros(m.cost(solver))}/week")


def pareto_table() -> pd.DataFrame:
    """§5: for each feasible plan, which plans beat it on both criteria, and why."""
    feasible = [p for p in m.all_plans() if m.is_feasible(p)]
    feasible.sort(key=m.cost)
    cheapest = min(feasible, key=m.cost)
    fastest = min(feasible, key=m.average_delivery_time)
    rows = {}
    for plan in feasible:
        cost, time = m.cost(plan), m.average_delivery_time(plan)
        reasons = m.beaten_by(plan, feasible)
        if len(reasons) == 1:
            other = reasons[0]
            beaten = (f"{m.name_of(other)}: cheaper ({m.cost(other):g} < {cost:g}) "
                      f"and faster ({m.average_delivery_time(other):.2f} < {time:.2f})")
        elif reasons:
            beaten = (", ".join(m.name_of(o) for o in reasons)
                      + f": each one is cheaper and faster than {m.name_of(plan)}")
        elif plan == cheapest:
            beaten = "none: no feasible plan is cheaper"
        elif plan == fastest:
            beaten = "none: no feasible plan is faster"
        else:
            beaten = "none"
        rows[m.name_of(plan)] = {
            "Cost (€/week)": cost,
            "Average delivery time (days)": f"{time:.2f}",
            "Beaten by": beaten,
            "Pareto-optimal": "yes" if not reasons else "no",
        }
    return pd.DataFrame(rows).T.rename_axis("Plan")


def _plot_plans(ax, chosen: dict | None = None) -> None:
    plans = m.all_plans()
    feasible = [p for p in plans if m.is_feasible(p)]
    for p in plans:
        x, y = m.average_delivery_time(p), m.cost(p)
        if not m.is_feasible(p):
            ax.scatter(x, y, marker="x", color="0.7", zorder=2)
            continue
        pareto = m.is_pareto_optimal(p, feasible)
        ax.scatter(x, y, s=120, zorder=3, color="tab:green" if pareto else "0.35",
                   edgecolor="black" if p == chosen else "none", lw=2)
        ax.annotate(m.name_of(p), (x, y), xytext=(9, 6), textcoords="offset points",
                    weight="bold" if p == chosen else "normal")
    b, plan_m = m.NAMED_PLANS["B"], m.NAMED_PLANS["M"]
    ax.annotate("", xy=(m.average_delivery_time(b), m.cost(b)),
                xytext=(m.average_delivery_time(plan_m), m.cost(plan_m)),
                arrowprops=dict(arrowstyle="->", color="tab:green", lw=1.5))
    ax.scatter([], [], s=80, color="tab:green", label="Pareto-optimal (feasible)")
    ax.scatter([], [], s=80, color="0.35", label="feasible, beaten by another plan")
    ax.scatter([], [], marker="x", color="0.7", label="not feasible")
    ax.set_xlim(0.9, 3.0)
    ax.set_ylim(250, 800)
    ax.set_xlabel("Average delivery time (days)")
    ax.set_ylabel("Cost (€/week)")
    ax.spines[["top", "right"]].set_visible(False)


@_light
def pareto() -> None:
    """§5: the 16 plans on both criteria, and which feasible plans are Pareto-optimal."""
    fig, ax = plt.subplots(figsize=(8, 4.8))
    _plot_plans(ax)
    ax.legend(fontsize=8, loc="upper left")
    plt.show()
    _display(pareto_table())


@_light
def two_objectives(value_of_a_day: float) -> None:
    """§5: the plan chosen with the single objective cost + V x average delivery time."""
    v = value_of_a_day
    chosen = m.solve_weighted(v)
    best_total = m.total(chosen, v)
    fig, ax = plt.subplots(figsize=(8, 4.8))
    _plot_plans(ax, chosen)
    # All points with the same total as the chosen plan: cost = total - V x time,
    # a line with slope -V. Feasible plans above it have a higher total.
    xs = [0.9, 3.0]
    ax.plot(xs, [best_total - v * x for x in xs], color="black", ls=":", lw=1.2,
            label=f"cost + {v:g} × time = {best_total:.0f} €/week (slope −{v:g})")
    ax.legend(fontsize=8, loc="upper left")
    plt.show()

    print(f"V = {v:g} €/week per day: the company would pay up to {_euros(v)} a week "
          "to make the average delivery one day shorter.")
    feasible = sorted((p for p in m.all_plans() if m.is_feasible(p)), key=lambda p: m.total(p, v))
    _display(pd.DataFrame({
        m.name_of(p): {
            "Cost (€/week)": m.cost(p),
            "Average delivery time (days)": f"{m.average_delivery_time(p):.2f}",
            f"V × time (€/week)": f"{v * m.average_delivery_time(p):.0f}",
            "Total (€/week)": f"{m.total(p, v):.0f}",
        } for p in feasible}).T.rename_axis("Plan"))
    print(f"Best plan (solver, objective cost + V × time): {m.name_of(chosen)}, "
          f"total {best_total:.0f} €/week.")
    a, b = m.NAMED_PLANS["A"], m.NAMED_PLANS["B"]
    extra = m.cost(b) - m.cost(a)
    saved = m.average_delivery_time(a) - m.average_delivery_time(b)
    switch = m.switch_value(a, b)
    print(f"From A to B: {_euros(extra)}/week more, {saved:.3f} days faster on average. "
          f"Each day saved costs {extra:g} / {saved:.3f} = {switch:.0f} €/week.")
    print(f"So A is chosen when V is below {switch:.0f} €/week per day, and B when V is above.")


def forecast_table() -> pd.DataFrame:
    """Table 8: orders of C3, 4-week moving average and error."""
    table = pd.DataFrame({
        "Orders": orders_C3,
        "Forecast": fc.moving_average(),
        "Error (orders − forecast)": fc.errors(),
    }, index=pd.RangeIndex(1, len(orders_C3) + 1, name="Week")).T
    return table.round(2).astype(object).where(table.notna(), "—")


@_light
def show_forecast() -> None:
    """Table 8, its accuracy and a figure with orders, forecast and week 13."""
    _display(forecast_table())
    acc = fc.accuracy()
    print(f"MAE {acc['MAE']:.2f} pallets/week · MAPE {acc['MAPE']:.1f} % · "
          f"bias {acc['bias']:.2f} pallets/week (weeks 5-12)")
    print(f"Forecast for week 13: {fc.next_week():g} pallets")
    weeks = range(1, len(orders_C3) + 1)
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(weeks, orders_C3, marker="o", label="Orders")
    ax.plot(weeks, fc.moving_average(), marker="s", ls="--", label="Forecast (4-week average)")
    ax.scatter([13], [fc.next_week()], marker="s", color="tab:orange", zorder=3)
    ax.scatter([13], [order_C3_week13], marker="o", color=OVER, s=70, zorder=3,
               label=f"Week 13: {order_C3_week13} pallets ordered")
    ax.set_xticks(range(1, 14))
    ax.set_xlabel("Week")
    ax.set_ylabel("Pallets/week")
    ax.set_ylim(25, 50)
    ax.legend(fontsize=8, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()


def large_error(c3_order: float) -> None:
    """§6: plan A when C3 orders c3_order pallets, and the plan recomputed with that order."""
    demand = dict(d, C3=c3_order)
    print(f"C3 orders {c3_order:g} pallets; the forecast was {d['C3']} "
          f"({c3_order - d['C3']:+g}).")
    check_plan(m.NAMED_PLANS["A"], "Plan A with the new order of C3", demand=demand)
    print()
    new = m.solve(demand=demand)
    if new is None:
        print("Re-planning: no plan fits in the warehouses with this order.")
    elif new == m.NAMED_PLANS["A"]:
        print("Re-planning with the new order: plan A is still the best plan.")
    else:
        print(f"Re-planning with the new order: the best plan is now {m.name_of(new) or 'another one'}, "
              f"at {_euros(m.cost(new, demand))}/week.")
        _display(plan_table({"Re-planned": new}, demand))


def safety_margin(reserve_percent: float, c3_order: float) -> None:
    """§6: plan with part of the capacity in reserve, and whether it holds a large order of C3."""
    capacity = m.with_reserve(reserve_percent / 100)
    plan = m.solve(capacity)
    cost_a = m.cost(m.NAMED_PLANS["A"])
    print(f"Reserve {reserve_percent:g} %: W1 plans with {capacity['W1']:g} pallets, "
          f"W2 with {capacity['W2']:g}.")
    if plan is None:
        print(f"No plan fits: the customers need {sum(d.values())} pallets and the warehouses "
              f"can plan with only {sum(capacity.values()):g}.")
        return
    print(f"Best plan: {m.name_of(plan)}, {_euros(m.cost(plan))}/week. "
          f"The margin costs {_euros(m.cost(plan) - cost_a)}/week.")
    print()
    check_plan(plan, f"Plan {m.name_of(plan)} when C3 orders {c3_order:g} pallets",
               demand=dict(d, C3=c3_order))


# ---------------------------------------------------------------------------
# §7 Plans under uncertain demand
# ---------------------------------------------------------------------------

def _plan(name: str) -> dict:
    if name not in m.NAMED_PLANS:
        raise ValueError(f"The plan must be one of {', '.join(m.NAMED_PLANS)}.")
    return m.NAMED_PLANS[name]


def orders_table() -> pd.DataFrame:
    """Table 9: orders of C1 and C3, weeks 1 to 13 (pallets/week)."""
    from . import uncertain as u
    weeks = range(1, 14)
    return pd.DataFrame({f"{c}": [u.week_orders(w)[c] for w in weeks] for c in u.ORDERS},
                        index=pd.Index(weeks, name="Week")).T


def show_orders() -> None:
    """Table 9 and the orders of C2 and C4."""
    _display(orders_table())
    print(f"C2 and C4 order the same every week, by contract: {d['C2']} and {d['C4']} pallets.")


def summary_table() -> pd.DataFrame:
    """Table 10: weeks over capacity and smallest margin of each plan, weeks 1-12, and the
    pallets not served in week 13."""
    from . import uncertain as u
    rows = {}
    for name, plan in m.NAMED_PLANS.items():
        s = u.summary(plan)
        over = s["weeks over capacity"]
        lost = u.unserved(plan, u.week_orders(13))
        rows[name] = {
            "Weeks over capacity (1-12)": ", ".join(f"{wk} ({w})" for wk, w in over) or "none",
            **{f"Smallest margin {w} (pallets)": s["smallest margin"][w] for w in W},
            "Not served in week 13 (pallets)": ", ".join(f"{v} ({w})" for w, v in lost.items() if v) or "0",
        }
    return pd.DataFrame(rows).T.rename_axis("Plan")


@_light
def plan_by_week(plan_name: str, weeks: str = "1-12") -> None:
    """A plan week by week: loads, margins and pallets not served, a figure of the loads
    against the capacities, and Table 10."""
    from . import uncertain as u
    plan = _plan(plan_name)
    weeks = range(1, 13) if weeks == "1-12" else [13]
    rows = u.week_by_week(plan, weeks)
    print(f"Plan {plan_name}: " + ", ".join(f"{c} from {plan[c]}" for c in C))
    _display(pd.DataFrame(rows).set_index("week").rename_axis("Week").T)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    x = [r["week"] for r in rows]
    for w in W:
        y = [r[f"load {w}"] for r in rows]
        ax.plot(x, y, marker="o", color=COLOURS[w], label=f"Load {w}")
        ax.axhline(K[w], color=COLOURS[w], ls="--", lw=1, label=f"Capacity {w} ({K[w]})")
        over = [(xi, yi) for xi, yi in zip(x, y) if yi > K[w]]
        if over:
            ax.scatter(*zip(*over), s=110, facecolor="none", edgecolor=OVER, lw=2, zorder=3)
    ax.scatter([], [], s=110, facecolor="none", edgecolor=OVER, lw=2, label="Above capacity")
    ax.set_xticks(x)
    ax.set_xlabel("Week")
    ax.set_ylabel("Pallets/week")
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8, loc="lower right", ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()
    print("The five plans, weeks 1-12, and the pallets not served in week 13 (Table 10):")
    _display(summary_table())


def customer_forecast(customer: str, plan_name: str) -> None:
    """Forecast and error of C1 or C3 (Table 11), and, for a plan, the sum of the errors of
    the customers that share a warehouse."""
    from . import uncertain as u
    if customer not in u.ORDERS:
        raise ValueError("The customer must be C1 or C3: the others order the same every week.")
    orders = u.ORDERS[customer]
    table = pd.DataFrame({
        "Orders": orders,
        "Forecast": fc.moving_average(orders),
        "Error (orders − forecast)": fc.errors(orders),
    }, index=pd.RangeIndex(1, len(orders) + 1, name="Week")).T
    _display(table.round(2).astype(object).where(table.notna(), "—"))
    acc = fc.accuracy(orders)
    largest, week = fc.largest_positive_error(orders)
    print(f"{customer}, weeks 5-12: MAE {acc['MAE']:.2f} pallets/week · MAPE {acc['MAPE']:.1f} % · "
          f"bias {acc['bias']:.2f} pallets/week · largest positive error {largest:.2f} (week {week})")
    print(f"Forecast for week 13: {fc.next_week(orders):.2f} pallets")
    print()
    plan = _plan(plan_name)
    shared = u.shared_errors(plan)
    if not shared:
        print(f"In plan {plan_name}, C1 and C3 are served from different warehouses: "
              "their errors do not add up in any warehouse.")
        return
    for w, series in shared.items():
        names = " and ".join(c for c in u.ORDERS if plan[c] == w)
        print(f"In plan {plan_name}, {w} serves {names}. Sum of their errors, weeks 5-12 (pallets):")
        _display(pd.DataFrame({"Sum of errors": series}, index=pd.RangeIndex(5, 5 + len(series), name="Week")).T)
        top = max(series)
        print(f"Largest sum: {top:.2f} (week {5 + series.index(top)})")


def period_cost_table(n_weeks: int, pallet_cost: float, surprise_weeks: int,
                      c1_order: float, c3_order: float) -> pd.DataFrame:
    """Table 12: the cost of each plan kept for n_weeks, ordered from the cheapest."""
    from . import uncertain as u
    rows = {}
    for name, plan in m.NAMED_PLANS.items():
        c = u.period_cost(plan, n_weeks, pallet_cost, surprise_weeks, c1_order, c3_order)
        rows[name] = {"Weekly cost c (€/week)": c["weekly cost"],
                      "Not served in a surprise week (pallets)": c["not served in a surprise week"],
                      "Not served in the period U (pallets)": c["not served"],
                      "Total cost N·c + p·U (€)": c["total"]}
    table = pd.DataFrame(rows).T.rename_axis("Plan")
    return table.sort_values("Total cost N·c + p·U (€)", kind="stable")


@_light
def period_costs(n_weeks: int, pallet_cost: float, surprise_weeks: int,
                 c1_order: float, c3_order: float) -> None:
    """Table 12 and a bar chart of the total cost of each plan."""
    if surprise_weeks > n_weeks:
        print(f"The weeks with a surprise ({surprise_weeks}) cannot be more than the weeks of the "
              f"period ({n_weeks}). Lower s or raise N.")
        return
    print(f"N = {n_weeks} weeks · p = {_euros(pallet_cost)}/pallet · s = {surprise_weeks} weeks with a "
          f"surprise, in which C1 orders {c1_order:g} and C3 orders {c3_order:g} pallets")
    table = period_cost_table(n_weeks, pallet_cost, surprise_weeks, c1_order, c3_order)
    _display(table)
    fig, ax = plt.subplots(figsize=(7, 3.4))
    totals = table["Total cost N·c + p·U (€)"]
    bars = ax.bar(totals.index, totals.values, color="0.55")
    bars[0].set_color("tab:green")
    for bar, value in zip(bars, totals.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value, f"{value:,.0f} €", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel(f"Total cost over {n_weeks} weeks (€)")
    ax.set_xlabel("Plan, from the cheapest")
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()
