"""The linear model of §2, written with PuLP and solved with HiGHS, with its
shadow prices, reduced costs and the ranges in which a shadow price holds.

A capacity and a demand are given as dicts: capacity[f][t] (bikes/month) and
demand[t] (bikes/month). The capacities are written as constraints, not as
bounds of the variables, so that each one has its own shadow price.
"""

from __future__ import annotations

import pulp

from .data import F, K, REDUCED_F, REDUCED_T, T, c, d

TOL = 1e-6


def _optimal(result) -> bool:
    """True if the solver found an optimal solution. PuLP 3 returns the status as
    a number and PuLP 4 as an object with a field status; 1 is optimal in both."""
    return getattr(result, "status", result) == 1


def _constraints(model) -> dict:
    """The constraints of a model by name: a method in PuLP 4, a dict in PuLP 3."""
    constraints = model.constraints() if callable(model.constraints) else model.constraints
    return dict(constraints) if isinstance(constraints, dict) else {con.name: con for con in constraints}


def solve(plants=F, months=T, demand: dict = d, capacity: dict = K) -> dict | None:
    """Solve the model. Returns the cost (EUR), the plan p[f, t] (bikes), the shadow
    price of each demand and capacity (EUR/bike), the reduced cost of each variable
    (EUR/bike) and the spare capacity (bikes), or None if the model has no solution."""
    model = pulp.LpProblem("production_plan", pulp.LpMinimize)
    # p[f, t] = bikes assembled in plant f in month t (continuous, >= 0)
    p = {(f, t): model.add_variable(f"p_{f.replace(' ', '')}_{t}", lowBound=0)
         for f in plants for t in months}
    # Minimise the assembly cost
    model += pulp.lpSum(c[f] * p[f, t] for f in plants for t in months)
    # The demand of each month is assembled that month
    for t in months:
        model += (pulp.lpSum(p[f, t] for f in plants) >= demand[t], f"demand_{t}")
    # No plant assembles more than its capacity
    for f in plants:
        for t in months:
            model += (p[f, t] <= capacity[f][t], f"capacity_{f.replace(' ', '')}_{t}")

    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    cons = _constraints(model)
    clean = lambda v: 0.0 if abs(v) < TOL else v      # noqa: E731  (no "-0.0" in tables)
    return {
        "cost": pulp.value(model.objective),
        "plan": {(f, t): clean(p[f, t].value()) for f in plants for t in months},
        "demand price": {t: clean(cons[f"demand_{t}"].pi) for t in months},
        "capacity price": {(f, t): clean(cons[f"capacity_{f.replace(' ', '')}_{t}"].pi)
                           for f in plants for t in months},
        "reduced cost": {(f, t): clean(p[f, t].dj) for f in plants for t in months},
        "spare": {(f, t): clean(capacity[f][t] - p[f, t].value()) for f in plants for t in months},
    }


# ---------------------------------------------------------------------------
# Ranges: re-solve the model with the right-hand side changed
# ---------------------------------------------------------------------------

def _changed(kind: str, key, value: float, demand: dict, capacity: dict) -> tuple[dict, dict]:
    if kind == "demand":
        return dict(demand, **{key: value}), capacity
    f, t = key
    new = {g: dict(capacity[g]) for g in capacity}
    new[f][t] = value
    return demand, new


def validity_range(kind: str, key, plants=F, months=T, demand: dict = d, capacity: dict = K,
                   limit: float = 1e6) -> tuple[float | None, float | None]:
    """The values of one right-hand side (kind "demand", key t; or kind "capacity",
    key (f, t)) for which its shadow price holds: the model is re-solved with the
    right-hand side changed, and the shadow price holds while the cost changes by
    exactly the shadow price for each bike (steps of one bike). None: no limit.

    The cost is a convex piecewise linear function of the right-hand side, so the
    values that pass form an interval, found by doubling the step and then halving it."""
    base = solve(plants, months, demand, capacity)
    if base is None:
        raise ValueError("The model has no solution: there is no shadow price.")
    rhs = demand[key] if kind == "demand" else capacity[key[0]][key[1]]
    price = base["demand price"][key] if kind == "demand" else base["capacity price"][key]

    def holds(value: float) -> bool:
        if value < 0:
            return False
        new = solve(plants, months, *_changed(kind, key, value, demand, capacity))
        return new is not None and abs(new["cost"] - (base["cost"] + price * (value - rhs))) < 1e-6

    ends = []
    for direction in (-1, 1):
        good, step = 0, 1
        while step <= limit and holds(rhs + direction * step):
            good, step = step, 2 * step
        if step > limit:
            ends.append(None)
            continue
        bad = step
        while bad - good > 1:
            middle = (good + bad) // 2
            if holds(rhs + direction * middle):
                good = middle
            else:
                bad = middle
        ends.append(rhs + direction * good)
    return ends[0], ends[1]


# ---------------------------------------------------------------------------
# Reduced version: two plants, one month, drawn in the plane (§3)
# ---------------------------------------------------------------------------

def vertices(k1: float = K["Plant 1"]["Jan"], k2: float = K["Plant 2"]["Jan"],
             demand: float = d["Jan"]) -> list[tuple[float, float]]:
    """Vertices of the feasible region of the reduced version: p1 <= k1, p2 <= k2,
    p1 + p2 >= demand, p1, p2 >= 0. Each vertex is where two of the lines meet."""
    lines = [((1, 0), k1), ((0, 1), k2), ((1, 1), demand), ((1, 0), 0), ((0, 1), 0)]
    found = []
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            (a1, b1), r1 = lines[i]
            (a2, b2), r2 = lines[j]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            x = (r1 * b2 - r2 * b1) / det
            y = (a1 * r2 - a2 * r1) / det
            feasible = (-TOL <= x <= k1 + TOL and -TOL <= y <= k2 + TOL and x + y >= demand - TOL)
            if feasible and all(abs(x - u) > TOL or abs(y - v) > TOL for u, v in found):
                found.append((x + 0.0, y + 0.0))
    return sorted(found)


def reduced(k1: float = K["Plant 1"]["Jan"], demand: float = d["Jan"]) -> dict | None:
    """Solve the reduced version with the capacity of plant 1 and the demand of January given."""
    capacity = {f: dict(K[f]) for f in REDUCED_F}
    capacity["Plant 1"]["Jan"] = k1
    return solve(REDUCED_F, REDUCED_T, {"Jan": demand}, capacity)


def reduced_cost_of(point: tuple[float, float]) -> float:
    """Assembly cost of a point (p1, p2) of the reduced version (EUR)."""
    return c["Plant 1"] * point[0] + c["Plant 2"] * point[1]


# ---------------------------------------------------------------------------
# Capacity against demand, month by month and cumulative (§5)
# ---------------------------------------------------------------------------

def monthly_capacity(plants=F, months=T, capacity: dict = K) -> dict:
    """Total capacity of the plants each month (bikes/month)."""
    return {t: sum(capacity[f][t] for f in plants) for t in months}


def shortfall(demand: dict, plants=F, months=T, capacity: dict = K) -> dict:
    """Bikes of demand above the total capacity, in the months where there are any."""
    total = monthly_capacity(plants, months, capacity)
    return {t: demand[t] - total[t] for t in months if demand[t] > total[t]}


def cumulative(demand: dict, plants=F, months=T, capacity: dict = K) -> list[dict]:
    """Cumulative demand and cumulative capacity, month by month (bikes)."""
    total = monthly_capacity(plants, months, capacity)
    rows, dem, cap = [], 0, 0
    for t in months:
        dem += demand[t]
        cap += total[t]
        rows.append({"month": t, "demand": demand[t], "capacity": total[t], "spare": total[t] - demand[t],
                     "cumulative demand": dem, "cumulative capacity": cap})
    return rows
