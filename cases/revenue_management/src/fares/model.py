"""The network model of the two flights, written with PuLP and solved with HiGHS;
the bid prices of the flights and of the tickets, the shadow prices of the forecast
demand, the range in which each of them holds, an offer of a tour operator and a
change in the forecast demand of a fare.

The seats of the aircraft are given as a dict capacity[l] (seats) and the demand
as a dict demand[p] (tickets), with p = (trip, fare). The demand of each fare of
each trip is written as a constraint, not as a bound of the variable, so that
it has its own shadow price.
"""

from __future__ import annotations

import pulp

from .data import OFFER_TRIP, USES, C, D, L, P, a, r

TOL = 1e-6


def _optimal(result) -> bool:
    """True if the solver found an optimal solution. PuLP 3 returns the status as
    a number and PuLP 4 as an object with a field status; 1 is optimal in both."""
    return getattr(result, "status", result) == 1


def _constraints(model) -> dict:
    """The constraints of a model by name: a method in PuLP 4, a dict in PuLP 3."""
    constraints = model.constraints() if callable(model.constraints) else model.constraints
    return dict(constraints) if isinstance(constraints, dict) else {con.name: con for con in constraints}


def _label(text: str) -> str:
    """A name PuLP accepts: letters, digits and underscores."""
    return "".join(ch if ch.isalnum() else "_" for ch in text.replace("→", "to").replace("–", "to"))


def _clean(v: float) -> float:
    return 0.0 if abs(v) < TOL else v                 # no "-0.0" in tables


def _with(values: dict, key, value) -> dict:
    """A copy of a dict with one entry changed. The key of a demand is a pair
    (trip, fare), which dict(values, **{key: value}) does not accept."""
    return {**values, key: value}


def _build(capacity: dict, demand: dict, offer: tuple | None):
    model = pulp.LpProblem("revenue_management", pulp.LpMaximize)
    # x[p] = tickets of trip and fare p put on sale (x_tf, continuous, >= 0)
    x = {p: model.add_variable(f"x_{_label(p[0])}_{_label(p[1])}", lowBound=0) for p in P}
    revenue = pulp.lpSum(r[p] * x[p] for p in P)
    # An offer of n seats of a trip at q EUR/seat, forced into the plan (one seat on each flight of the trip)
    y = None
    if offer is not None:
        n, q = offer
        y = model.add_variable("offer", lowBound=0)
        model += (y == n, "offer")
        revenue += q * y
    # Maximise the revenue
    model += revenue
    # Seats of the aircraft: the seats used on each flight do not exceed them
    for l in L:
        used = pulp.lpSum(a(p, l) * x[p] for p in P)
        if y is not None and l in USES[OFFER_TRIP]:
            used += y
        model += (used <= capacity[l], f"capacity_{_label(l)}")
    # Forecast demand: no fare of a trip sells more tickets than its forecast demand
    for p in P:
        model += (x[p] <= demand[p], f"demand_{_label(p[0])}_{_label(p[1])}")
    return model, x, revenue


def solve(capacity: dict = C, demand: dict = D, offer: tuple | None = None) -> dict | None:
    """Solve the model. Returns the revenue (EUR), the plan x[p] (tickets), the seats
    used on each flight, the bid price of each flight (EUR/seat), the shadow price of
    the demand of each fare of each trip (EUR/ticket), the spare seats of each flight
    and the unsold demand of each fare of each trip (tickets); None if the model has no solution.

    offer = (n, q): n seats of the trip OFFER_TRIP sold at q EUR/seat on top of the plan."""
    model, x, _ = _build(capacity, demand, offer)
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    cons = _constraints(model)
    plan = {p: _clean(x[p].value()) for p in P}
    extra = offer[0] if offer is not None else 0
    seats = {l: _clean(sum(a(p, l) * plan[p] for p in P) + (extra if l in USES[OFFER_TRIP] else 0)) for l in L}
    # HiGHS returns the shadow prices of the minimisation it solves inside, so in
    # this maximisation their sign is the opposite of the change in revenue.
    # The minus sign gives them as the rise in revenue when the right-hand side
    # grows by one unit (checked by re-solving, in the tests).
    return {
        "revenue": _clean(pulp.value(model.objective)),
        "plan": plan,
        "seats": seats,
        "bid price": {l: _clean(-cons[f"capacity_{_label(l)}"].pi) for l in L},
        "demand price": {p: _clean(-cons[f"demand_{_label(p[0])}_{_label(p[1])}"].pi) for p in P},
        "spare seats": {l: _clean(capacity[l] - seats[l]) for l in L},
        "unsold demand": {p: _clean(demand[p] - plan[p]) for p in P},
    }


def plan_bounds(capacity: dict = C, demand: dict = D) -> dict:
    """Smallest and largest value of each x[p] among the plans with the optimal
    revenue. The optimal plan is unique if the two coincide for every fare of every trip."""
    best = solve(capacity, demand)["revenue"]
    bounds = {}
    for p in P:
        ends = []
        for sense in (pulp.LpMinimize, pulp.LpMaximize):
            model, x, revenue = _build(capacity, demand, None)
            model += (revenue >= best - TOL, "optimal_revenue")
            model.sense = sense
            model.setObjective(x[p])
            model.solve(pulp.HiGHS(msg=False))
            ends.append(_clean(x[p].value()))
        bounds[p] = tuple(ends)
    return bounds


def changed_tickets(base: dict, new: dict) -> dict:
    """Fares of the trips whose tickets change between two plans: {p: (before, after)}."""
    return {p: (base[p], new[p]) for p in P if abs(base[p] - new[p]) > TOL}


# ---------------------------------------------------------------------------
# Bid prices
# ---------------------------------------------------------------------------

def product_bid_price(p, bid: dict) -> float:
    """Bid price b_tf of a ticket of p = (trip, fare): the bid prices of the flights of
    its trip times the seats it uses on each (Ivanov et al., 2025, Eq. 18.15)."""
    return sum(a(p, l) * bid[l] for l in L)


def trip_bid_price(trip: str, bid: dict) -> float:
    """Bid price of one seat on each flight of a trip (EUR/seat)."""
    return sum(bid[l] for l in USES[trip])


def change_capacity(flight: str, delta: float, capacity: dict = C, demand: dict = D) -> float:
    """Change in the optimal revenue when the seats of the aircraft of a flight change by
    delta seats."""
    base = solve(capacity, demand)
    new = solve(_with(capacity, flight, capacity[flight] + delta), demand)
    return new["revenue"] - base["revenue"]


def seat_change(flight: str, capacity: dict = C, demand: dict = D) -> list[dict]:
    """Fares of the trips whose tickets change when the aircraft of a flight has one seat
    less or one seat more:
    tickets with one seat less, in the optimal plan and with one seat more, and the
    change in revenue each one brings with one seat more (EUR). The changes with one
    seat more add up to the bid price of the flight."""
    plans = [solve(_with(capacity, flight, capacity[flight] + delta), demand)["plan"] for delta in (-1, 0, 1)]
    less, base, more = plans
    rows = [{"product": p, "less": less[p], "plan": base[p], "more": more[p], "change": r[p] * (more[p] - base[p])}
            for p in P if abs(less[p] - base[p]) > TOL or abs(more[p] - base[p]) > TOL]
    # First the tickets that take the extra seat, then those it displaces
    return sorted(rows, key=lambda row: -row["change"])


# ---------------------------------------------------------------------------
# The range in which a shadow price holds
# ---------------------------------------------------------------------------

def validity_range(side: str, key, capacity: dict = C, demand: dict = D,
                   limit: float = 1e6) -> tuple[float | None, float | None]:
    """The values of a right-hand side for which its shadow price holds: the model is
    re-solved with that right-hand side changed, and the shadow price holds while the
    revenue changes by exactly the shadow price for each unit. None: no limit.

    side = "seats": key is a flight, the right-hand side its seats (seats) and the
    shadow price its bid price. side = "demand": key is a fare of a trip, p = (trip,
    fare), the right-hand side its forecast demand (tickets) and the shadow price the
    shadow price of that demand.

    The revenue is a concave piecewise linear function of each right-hand side, so the
    values that pass form an interval. Its ends are found by doubling the step and then
    halving it; an end between two whole numbers is found by halving further, to a
    millionth."""
    base = solve(capacity, demand)
    if side == "seats":
        start, price = capacity[key], base["bid price"][key]
        def resolve(value):
            return solve(_with(capacity, key, value), demand)
    elif side == "demand":
        start, price = demand[key], base["demand price"][key]
        def resolve(value):
            return solve(capacity, _with(demand, key, value))
    else:
        raise ValueError('The side must be "seats" or "demand".')

    def holds(value: float) -> bool:
        if value < 0:
            return False
        new = resolve(value)
        return new is not None and abs(new["revenue"] - (base["revenue"] + price * (value - start))) < TOL

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


def _inside(value: float, low, high) -> bool:
    return (low is None or value >= low - TOL) and (high is None or value <= high + TOL)


# ---------------------------------------------------------------------------
# Offer of a tour operator and change in the forecast demand of a fare
# ---------------------------------------------------------------------------

def offer(seats: float, price: float, capacity: dict = C, demand: dict = D) -> dict | None:
    """An offer of seats of OFFER_TRIP at price EUR/seat, on top of the forecast demand.
    The change in revenue found by solving again with the offer forced into the plan,
    against the estimate with the bid prices: seats × (price − bid price of the trip).
    None if the offer does not fit in the flights."""
    base = solve(capacity, demand)
    new = solve(capacity, demand, offer=(seats, price))
    if new is None:
        return None
    bid = trip_bid_price(OFFER_TRIP, base["bid price"])
    return {"base": base, "new": new, "trip bid price": bid,
            "change": new["revenue"] - base["revenue"], "estimate": seats * (price - bid)}


def demand_change(product, new_demand: float, cost: float = 0, capacity: dict = C,
                  demand: dict = D) -> dict:
    """A change in the forecast demand of one fare of one trip, p = (trip, fare), to
    new_demand tickets, at a cost of cost EUR (a marketing campaign, for example): the
    shadow price of that demand in the optimal plan (EUR/ticket), the range of the
    demand for which it holds (tickets), whether new_demand is inside the range, the
    estimate with the shadow price, the change in revenue found by solving again, the
    bid prices of the flights with the new demand, the fares of the trips whose tickets
    change and the net result, with the estimate and solving again."""
    base = solve(capacity, demand)
    new = solve(capacity, _with(demand, product, new_demand))
    price = base["demand price"][product]
    low, high = validity_range("demand", product, capacity, demand)
    estimate = price * (new_demand - demand[product])
    change = new["revenue"] - base["revenue"]
    return {"product": product, "demand": new_demand, "base": base, "new": new,
            "shadow price": price, "estimate": estimate, "change": change,
            "range": (low, high), "inside": _inside(new_demand, low, high),
            "changed": changed_tickets(base["plan"], new["plan"]),
            "cost": cost, "net": change - cost, "net estimate": estimate - cost}
