"""The linear model of §2, written with PuLP and solved with HiGHS, with its
slacks, its shadow prices, the ranges in which a shadow price holds and the
revenue against the capacity of the cabin.

A demand is given as a dict demand[f] (tickets) and the capacity as a number
(seats). The demand of each fare is written as a constraint, not as a bound of
the variable, so that it has its own shadow price.

A constraint is named by a key: "capacity" for the capacity of the cabin, or
the name of a fare for the demand of that fare.
"""

from __future__ import annotations

import pulp

from .data import CURVE, C, D, F, a, r

TOL = 1e-6
CAPACITY = "capacity"
KEYS = [CAPACITY] + F


def name(key: str) -> str:
    """Name of a constraint in the tables: "Capacity of the cabin" or "Demand of <fare>"."""
    return "Capacity of the cabin" if key == CAPACITY else f"Demand of {key}"


def _optimal(result) -> bool:
    """True if the solver found an optimal solution. PuLP 3 returns the status as
    a number and PuLP 4 as an object with a field status; 1 is optimal in both."""
    return getattr(result, "status", result) == 1


def _constraints(model) -> dict:
    """The constraints of a model by name: a method in PuLP 4, a dict in PuLP 3."""
    constraints = model.constraints() if callable(model.constraints) else model.constraints
    return dict(constraints) if isinstance(constraints, dict) else {con.name: con for con in constraints}


def _label(fare: str) -> str:
    return fare.replace(" ", "_")


def solve(capacity: float = C, demand: dict = D, fares=F) -> dict:
    """Solve the model. Returns the revenue (EUR), the plan x[f] (tickets), the seats
    used, the shadow price of the capacity (the bid price, EUR/seat) and of each
    demand (EUR/ticket), the spare seats and the unsold demand of each fare (tickets)."""
    model = pulp.LpProblem("revenue_management", pulp.LpMaximize)
    # x[f] = tickets of fare f put on sale (continuous, >= 0)
    x = {f: model.add_variable(f"x_{_label(f)}", lowBound=0) for f in fares}
    # Maximise the revenue
    model += pulp.lpSum(r[f] * x[f] for f in fares)
    # The tickets on sale fit in the cabin
    model += (pulp.lpSum(a[f] * x[f] for f in fares) <= capacity, "capacity")
    # No fare sells more tickets than its forecast demand
    for f in fares:
        model += (x[f] <= demand[f], f"demand_{_label(f)}")

    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        raise RuntimeError("The solver did not find an optimal solution.")
    cons = _constraints(model)
    clean = lambda v: 0.0 if abs(v) < TOL else v      # noqa: E731  (no "-0.0" in tables)
    # HiGHS returns the shadow prices of the minimisation it solves inside, so in
    # this maximisation their sign is the opposite of the change in revenue.
    # The minus sign gives them as the rise in revenue when the right-hand side
    # grows by one unit (checked by re-solving, in the tests).
    plan = {f: clean(x[f].value()) for f in fares}
    seats = sum(a[f] * plan[f] for f in fares)
    return {
        "revenue": clean(pulp.value(model.objective)),
        "plan": plan,
        "seats": clean(seats),
        "bid price": clean(-cons["capacity"].pi),
        "demand price": {f: clean(-cons[f"demand_{_label(f)}"].pi) for f in fares},
        "spare seats": clean(capacity - seats),
        "unsold demand": {f: clean(demand[f] - plan[f]) for f in fares},
    }


def shadow_price(solution: dict, key: str) -> float:
    """Shadow price of a constraint: EUR/seat for the capacity, EUR/ticket for a demand."""
    return solution["bid price"] if key == CAPACITY else solution["demand price"][key]


def slack(solution: dict, key: str) -> float:
    """Slack of a constraint: spare seats for the capacity, unsold tickets for a demand."""
    return solution["spare seats"] if key == CAPACITY else solution["unsold demand"][key]


def rhs(key: str, capacity: float = C, demand: dict = D) -> float:
    """Right-hand side of a constraint."""
    return capacity if key == CAPACITY else demand[key]


def _changed(key: str, value: float, capacity: float, demand: dict) -> tuple[float, dict]:
    if key == CAPACITY:
        return value, demand
    return capacity, dict(demand, **{key: value})


def one_more(key: str, capacity: float = C, demand: dict = D) -> dict:
    """Solve again with the right-hand side of a constraint one unit higher. Returns
    the revenue before and after, the change and the shadow price, to compare them."""
    base = solve(capacity, demand)
    new = solve(*_changed(key, rhs(key, capacity, demand) + 1, capacity, demand))
    return {"revenue": base["revenue"], "revenue with one more": new["revenue"],
            "change": new["revenue"] - base["revenue"], "shadow price": shadow_price(base, key)}


# ---------------------------------------------------------------------------
# Ranges: re-solve the model with the right-hand side changed
# ---------------------------------------------------------------------------

def validity_range(key: str, capacity: float = C, demand: dict = D,
                   limit: float = 1e6) -> tuple[float | None, float | None]:
    """The values of one right-hand side for which its shadow price holds: the model
    is re-solved with the right-hand side changed, and the shadow price holds while
    the revenue changes by exactly the shadow price for each unit. None: no limit.

    The revenue is a concave piecewise linear function of the right-hand side, so
    the values that pass form an interval. Its ends are found by doubling the step
    and then halving it; an end between two whole numbers (a limit of 66.67 tickets)
    is found by halving further, to a millionth."""
    base = solve(capacity, demand)
    start = rhs(key, capacity, demand)
    price = shadow_price(base, key)

    def holds(value: float) -> bool:
        if value < 0:
            return False
        new = solve(*_changed(key, value, capacity, demand))
        return abs(new["revenue"] - (base["revenue"] + price * (value - start))) < TOL

    ends = []
    for direction in (-1, 1):
        good, step = 0, 1
        while step <= limit and holds(start + direction * step):
            good, step = step, 2 * step
        if step > limit:
            ends.append(None)
            continue
        bad = step
        while bad - good > TOL:
            middle = (good + bad) / 2 if bad - good <= 1 else (good + bad) // 2
            if holds(start + direction * middle):
                good = middle
            else:
                bad = middle
        end = start + direction * good
        ends.append(round(end) if abs(end - round(end)) < 1e-4 else end)
    return ends[0], ends[1]


# ---------------------------------------------------------------------------
# Revenue against the capacity of the cabin
# ---------------------------------------------------------------------------

def revenue_curve(low: int = CURVE[0], high: int = CURVE[1], demand: dict = D) -> list[tuple[int, float]]:
    """Optimal revenue (EUR) for every whole capacity from low to high (seats)."""
    return [(k, solve(k, demand)["revenue"]) for k in range(low, high + 1)]


def segments(low: int = CURVE[0], high: int = CURVE[1], demand: dict = D) -> list[dict]:
    """The straight pieces of the revenue curve: where each one starts and ends
    (seats), its slope (EUR/seat, the value of one more seat) and the fare whose
    tickets grow along it (None if no fare grows: the seats are left empty)."""
    curve = revenue_curve(low, high, demand)
    pieces = []
    for (k0, z0), (k1, z1) in zip(curve, curve[1:]):
        slope = z1 - z0
        if pieces and abs(pieces[-1]["slope"] - slope) < TOL:
            pieces[-1]["to"] = k1
        else:
            pieces.append({"from": k0, "to": k1, "slope": 0.0 if abs(slope) < TOL else slope})
    for piece in pieces:
        before, after = solve(piece["from"], demand)["plan"], solve(piece["to"], demand)["plan"]
        grows = [f for f in F if after[f] - before[f] > TOL]
        piece["fare"] = grows[0] if grows else None
    return pieces


def other_capacity(capacity: float, base_capacity: float = C, demand: dict = D) -> dict:
    """The plan with another capacity, compared with the plan with the base capacity:
    the change in revenue found by solving again, and the change estimated with the
    bid price of the base plan, which holds only inside its range."""
    base = solve(base_capacity, demand)
    new = solve(capacity, demand)
    low, high = validity_range(CAPACITY, base_capacity, demand)
    inside = (low is None or capacity >= low - TOL) and (high is None or capacity <= high + TOL)
    estimate = base["bid price"] * (capacity - base_capacity)
    return {"capacity": capacity, "base": base, "new": new,
            "change": new["revenue"] - base["revenue"], "estimate": estimate,
            "range": (low, high), "inside": inside}
