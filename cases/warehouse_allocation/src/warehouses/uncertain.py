"""§7 Plans under uncertain demand: a plan kept for several weeks while the orders change.

Assumptions (§7):

1. The plan is kept for a period of N weeks, with no changes.
2. Each customer is served from one warehouse. The pallets above the capacity of a
   warehouse in a week are not served: they are lost, and each one costs p EUR.
3. Each week is independent: no stock and no pending orders pass from one week to the next.
4. The cost of a plan in the period is its weekly cost (Table 6, with the forecast demand
   of Table 2) times N, plus p for each pallet not served.
"""

from __future__ import annotations

from . import forecast as fc
from . import model as m
from .data import C, K, W, d, order_C1_week13, order_C3_week13, orders_C1, orders_C3

ORDERS = {"C1": orders_C1, "C3": orders_C3}  # the customers whose orders change, weeks 1-12
WEEK13 = {"C1": order_C1_week13, "C3": order_C3_week13}
WEEKS = range(1, 13)


def week_orders(week: int) -> dict:
    """The orders of the four customers in a week, 1 to 13 (pallets)."""
    if not 1 <= week <= 13:
        raise ValueError("The orders are known for weeks 1 to 13.")
    orders = dict(d)  # C2 and C4: their demand every week
    for c, series in ORDERS.items():
        orders[c] = WEEK13[c] if week == 13 else series[week - 1]
    return orders


def unserved(plan: dict, orders: dict) -> dict:
    """Pallets above the capacity of each warehouse, which are not served."""
    load = m.loads(plan, orders)
    return {w: max(0, load[w] - K[w]) for w in W}


def week_by_week(plan: dict, weeks=WEEKS) -> list[dict]:
    """For each week: the load, the margin (capacity - load) and the pallets not served of
    each warehouse."""
    rows = []
    for week in weeks:
        orders = week_orders(week)
        load = m.loads(plan, orders)
        lost = unserved(plan, orders)
        rows.append({"week": week,
                     **{f"load {w}": load[w] for w in W},
                     **{f"margin {w}": K[w] - load[w] for w in W},
                     **{f"not served {w}": lost[w] for w in W}})
    return rows


def summary(plan: dict, weeks=WEEKS) -> dict:
    """The weeks with a load above capacity, with the warehouse, and the smallest margin of
    each warehouse in those weeks."""
    rows = week_by_week(plan, weeks)
    return {
        "weeks over capacity": [(r["week"], w) for r in rows for w in W if r[f"margin {w}"] < 0],
        "smallest margin": {w: min(r[f"margin {w}"] for r in rows) for w in W},
    }


def shared_errors(plan: dict) -> dict[str, list[float]]:
    """For each warehouse that serves more than one customer whose orders change, the sum
    of their forecast errors, week by week (weeks 5-12)."""
    shared = {}
    for w in W:
        customers = [c for c in ORDERS if plan[c] == w]
        if len(customers) > 1:
            series = [fc.errors(ORDERS[c]) for c in customers]
            shared[w] = [sum(e[i] for e in series) for i in range(len(series[0])) if series[0][i] is not None]
    return shared


def period_cost(plan: dict, n_weeks: int, pallet_cost: float, surprise_weeks: int,
                c1_order: float = order_C1_week13, c3_order: float = order_C3_week13) -> dict:
    """The cost of a plan kept for n_weeks: its weekly cost times n_weeks, plus
    pallet_cost for each pallet not served. In surprise_weeks of the period C1 and C3 order
    c1_order and c3_order; in the other weeks every customer orders its forecast demand."""
    if not 0 <= surprise_weeks <= n_weeks:
        raise ValueError("The weeks with a surprise must be between 0 and the weeks of the period.")
    lost_in_a_surprise = sum(unserved(plan, dict(d, C1=c1_order, C3=c3_order)).values())
    not_served = surprise_weeks * lost_in_a_surprise
    weekly = m.cost(plan)
    return {
        "weekly cost": weekly,
        "not served in a surprise week": lost_in_a_surprise,
        "not served": not_served,
        "total": n_weeks * weekly + pallet_cost * not_served,
    }
