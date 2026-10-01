"""Plans, their cost and delivery time, and the two ways of finding the best one.

A plan says which warehouse serves each customer, as a dict:
{"C1": "W1", "C2": "W2", "C3": "W1", "C4": "W2"} is plan A.
"""

from __future__ import annotations

import itertools

import pulp

from .data import C, K, W, d, k, t

# The feasible plans, named as in Table 6 (ordered by cost)
NAMED_PLANS = {
    "A": {"C1": "W1", "C2": "W2", "C3": "W1", "C4": "W2"},
    "B": {"C1": "W2", "C2": "W1", "C3": "W1", "C4": "W2"},
    "M": {"C1": "W1", "C2": "W1", "C3": "W2", "C4": "W2"},
    "D": {"C1": "W2", "C2": "W2", "C3": "W1", "C4": "W1"},
    "E": {"C1": "W1", "C2": "W2", "C3": "W2", "C4": "W1"},
}


def check(plan: dict) -> dict:
    """Stop with a clear message if a plan is not written correctly."""
    missing = [c for c in C if c not in plan]
    if missing:
        raise ValueError(f"The plan has no warehouse for {', '.join(missing)}.")
    wrong = [c for c in C if plan[c] not in W]
    if wrong:
        raise ValueError(f"The warehouse of {', '.join(wrong)} must be W1 or W2.")
    return {c: plan[c] for c in C}


def name_of(plan: dict) -> str | None:
    """The name of a plan in Table 6 (A, B, M, D, E), or None."""
    for name, named in NAMED_PLANS.items():
        if named == plan:
            return name
    return None


def loads(plan: dict, demand: dict = d) -> dict:
    """Pallets shipped by each warehouse in a plan."""
    return {w: sum(demand[c] for c in C if plan[c] == w) for w in W}


def is_feasible(plan: dict, capacity: dict = K, demand: dict = d) -> bool:
    """True if no warehouse ships more than its capacity."""
    load = loads(plan, demand)
    return all(load[w] <= capacity[w] for w in W)


def excess(plan: dict, capacity: dict = K, demand: dict = d) -> dict:
    """Pallets above capacity of each warehouse that is over capacity."""
    load = loads(plan, demand)
    return {w: load[w] - capacity[w] for w in W if load[w] > capacity[w]}


def cost(plan: dict, demand: dict = d) -> float:
    """Total shipping cost of a plan (EUR/week)."""
    return sum(k[plan[c]][c] * demand[c] for c in C)


def average_delivery_time(plan: dict) -> float:
    """Delivery time of each customer weighted by its pallets (days), §5."""
    return sum(t[plan[c]][c] * d[c] for c in C) / sum(d.values())


def nearest_warehouse_plan() -> dict:
    """Rule of thumb: each customer from its nearest (cheapest) warehouse."""
    return {c: min(W, key=lambda w: k[w][c]) for c in C}


def diverted_by_hand_plan() -> dict:
    """Plan M: customers one by one, in order C1, C2, C3, C4; each goes to its
    nearest warehouse, and if that warehouse has no room left, to the other."""
    plan, used = {}, {w: 0 for w in W}
    for c in C:
        nearest = min(W, key=lambda w: k[w][c])
        other = next(w for w in W if w != nearest)
        plan[c] = nearest if used[nearest] + d[c] <= K[nearest] else other
        used[plan[c]] += d[c]
    return plan


def all_plans() -> list[dict]:
    """The 2^4 = 16 plans: every way of choosing a warehouse for each customer."""
    return [dict(zip(C, choice)) for choice in itertools.product(W, repeat=len(C))]


def best_by_brute_force(capacity: dict = K, demand: dict = d) -> dict | None:
    """The cheapest feasible plan, found by checking all 16 plans."""
    feasible = [p for p in all_plans() if is_feasible(p, capacity, demand)]
    return min(feasible, key=lambda p: cost(p, demand)) if feasible else None


def solve(capacity: dict = K, demand: dict = d) -> dict | None:
    """The model of §2, written with PuLP and solved with HiGHS."""
    model = pulp.LpProblem("warehouse_allocation", pulp.LpMinimize)
    # x[w][c] = 1 if warehouse w serves customer c (integer between 0 and 1;
    # the bounds are explicit because PuLP 4.0.0 does not set them for binaries)
    x = model.add_variable_dicts("x", (W, C), lowBound=0, upBound=1, cat="Integer")
    model += pulp.lpSum(k[w][c] * demand[c] * x[w][c] for w in W for c in C)
    for c in C:
        model += pulp.lpSum(x[w][c] for w in W) == 1
    for w in W:
        model += pulp.lpSum(demand[c] * x[w][c] for c in C) <= capacity[w]
    model.solve(pulp.HiGHS(msg=False))
    # The plan: the warehouse w with x[w][c] = 1 for each customer c
    # (value() is None if the solver found no solution)
    plan = {c: w for c in C for w in W
            if x[w][c].value() is not None and x[w][c].value() > 0.5}
    return plan if len(plan) == len(C) and is_feasible(plan, capacity, demand) else None


def is_pareto_optimal(plan: dict, plans: list[dict]) -> bool:
    """True if no other plan is at least as good on both criteria and
    strictly better on one of them (§5)."""
    for other in plans:
        no_worse = (cost(other) <= cost(plan)
                    and average_delivery_time(other) <= average_delivery_time(plan))
        better = (cost(other) < cost(plan)
                  or average_delivery_time(other) < average_delivery_time(plan))
        if no_worse and better:
            return False
    return True


def beaten_by(plan: dict, plans: list[dict]) -> list[dict]:
    """The plans that beat a plan: no worse on both criteria and better on one."""
    return [other for other in plans
            if cost(other) <= cost(plan)
            and average_delivery_time(other) <= average_delivery_time(plan)
            and (cost(other) < cost(plan)
                 or average_delivery_time(other) < average_delivery_time(plan))]


def total(plan: dict, value_of_a_day: float) -> float:
    """Cost + value_of_a_day x average delivery time (EUR/week), §5."""
    return cost(plan) + value_of_a_day * average_delivery_time(plan)


def best_weighted(value_of_a_day: float) -> dict:
    """The feasible plan with the lowest total, found by checking all 16 plans."""
    feasible = [p for p in all_plans() if is_feasible(p)]
    return min(feasible, key=lambda p: total(p, value_of_a_day))


def solve_weighted(value_of_a_day: float, capacity: dict = K) -> dict | None:
    """The model of §5 with one objective, cost + V x average delivery time,
    written with PuLP and solved with HiGHS. The constraints are those of §2."""
    model = pulp.LpProblem("warehouse_allocation_two_objectives", pulp.LpMinimize)
    x = model.add_variable_dicts("x", (W, C), lowBound=0, upBound=1, cat="Integer")
    total_pallets = sum(d.values())
    model += (pulp.lpSum(k[w][c] * d[c] * x[w][c] for w in W for c in C)
              + value_of_a_day * pulp.lpSum(t[w][c] * d[c] * x[w][c] for w in W for c in C)
              / total_pallets)
    for c in C:
        model += pulp.lpSum(x[w][c] for w in W) == 1
    for w in W:
        model += pulp.lpSum(d[c] * x[w][c] for c in C) <= capacity[w]
    model.solve(pulp.HiGHS(msg=False))
    plan = {c: w for c in C for w in W
            if x[w][c].value() is not None and x[w][c].value() > 0.5}
    return plan if len(plan) == len(C) and is_feasible(plan, capacity) else None


def switch_value(cheaper: dict, faster: dict) -> float:
    """Value of a day (EUR/week per day) at which both plans have the same total:
    the extra cost of the faster plan divided by the days it saves."""
    return ((cost(faster) - cost(cheaper))
            / (average_delivery_time(cheaper) - average_delivery_time(faster)))


def with_reserve(reserve: float) -> dict:
    """Capacities with a share of each warehouse kept in reserve."""
    return {w: K[w] * (1 - reserve) for w in W}
