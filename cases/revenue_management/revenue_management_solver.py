# Revenue management - how many tickets of each fare of each trip an airline
# puts on sale on two connected flights
#
# This script reproduces every table of revenue_management.md (same folder):
# the flights, the trips and the fares (Tables 1 and 2), the optimal plan
# (Table 3), the binding constraints and their slack (Table 4), the bid prices
# of the flights checked by solving again (Table 5), the fares of the trips
# whose tickets change with one seat less and one seat more (Table 6), the bid
# prices of the tickets and the shadow prices of the demand (Table 7), the
# seats for which each bid price holds (Table 8), an offer of a tour operator
# (Table 9), the shadow price of the demand of each fare of each trip with the
# range in which it holds (Table 10) and a marketing campaign that would raise
# the demand of one fare (Table 11).
#
# The model is written with the PuLP library and solved by the HiGHS solver.
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later and two free libraries:
#   - PuLP: writes the optimisation model;
#   - highspy: the HiGHS solver, which solves the model written with PuLP.
#
# How to install them (only once), from a terminal:
#     Windows:          python -m pip install pulp highspy
#     macOS and Linux:  python3 -m pip install pulp highspy
# If you use Anaconda or Miniforge, activate your environment first
# (conda activate) and use "python" instead of "python3".
# To check that they are installed:
#     python3 -c "import pulp, highspy; print('OK')"      (python on Windows)
#
# How to run it (from this folder):
#     Windows:          python revenue_management_solver.py
#     macOS and Linux:  python3 revenue_management_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# §1 Data (Tables 1 and 2). Invented (2026)
# ---------------------------------------------------------------------------

# Flights l and the seats C[l] of the aircraft of each (seats)
L = ["BCN->RIX", "RIX->HEL"]
C = {"BCN->RIX": 220, "RIX->HEL": 140}

# Trips t and the flights each one uses (L_t): a BCN-HEL ticket needs a seat
# on both
TRIPS = ["BCN-RIX", "RIX-HEL", "BCN-HEL"]
USES = {"BCN-RIX": ["BCN->RIX"], "RIX-HEL": ["RIX->HEL"], "BCN-HEL": ["BCN->RIX", "RIX->HEL"]}

# Fares f and the seats s_f one ticket uses on each flight of its trip: a
# Business ticket leaves the middle seat free
FARES = ["Business", "Economy FLEX", "Economy BASIC"]
SEATS = {"Business": 1.5, "Economy FLEX": 1, "Economy BASIC": 1}

# The nine fares of the trips, each one a pair p = (trip, fare), written t, f
# in the document: price r[p] of a one-way ticket (EUR/ticket, r_tf) and
# forecast demand D[p] (tickets, D_tf)
P = [(trip, fare) for trip in TRIPS for fare in FARES]
r = dict(zip(P, [420, 180, 75,
                 200, 100, 45,
                 520, 230, 110]))
D = dict(zip(P, [16, 60, 160,
                 6, 40, 60,
                 6, 20, 80]))

# Offer of a tour operator (§4): seats BCN-HEL on top of the forecast demand
OFFER_TRIP = "BCN-HEL"
OFFERS = [(10, 100), (10, 120), (1, 120), (2, 120), (3, 120)]     # (seats, EUR/seat)

# Marketing campaign (§5): it would raise the forecast demand of this fare of
# this trip to CHANGE_DEMAND tickets and costs CHANGE_COST euros
CHANGE_PRODUCT = ("RIX-HEL", "Economy FLEX")
CHANGE_DEMAND = 50
CHANGE_COST = 600


def a(p, l):
    """Seats one ticket of p = (trip, fare) uses on flight l: s_f if its trip uses
    l, 0 if it does not."""
    trip, fare = p
    return SEATS[fare] if l in USES[trip] else 0


def label(text):
    """A name PuLP accepts: letters, digits and underscores."""
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def with_value(values, key, value):
    """A copy of a dict with one entry changed."""
    return {**values, key: value}


# ---------------------------------------------------------------------------
# §2 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(capacity, demand, offer=None):
    """Solve the model. Returns (revenue, plan, bid prices of the flights, shadow
    prices of the demand), or None if it has no solution. offer = (n, q): n seats
    of OFFER_TRIP at q EUR/seat, forced into the plan."""
    model = pulp.LpProblem("revenue_management", pulp.LpMaximize)

    # x[p] = tickets of trip and fare p put on sale (x_tf, continuous, >= 0)
    x = {p: model.add_variable(f"x_{label(p[0])}_{label(p[1])}", lowBound=0) for p in P}
    revenue = pulp.lpSum(r[p] * x[p] for p in P)

    # The offer: a variable fixed at n seats, one seat on each flight of its trip
    y = None
    if offer is not None:
        y = model.add_variable("offer", lowBound=0)
        model += (y == offer[0], "offer")
        revenue += offer[1] * y

    # Maximise the revenue
    model += revenue

    # Seats of the aircraft: the seats used on each flight do not exceed them
    for l in L:
        used = pulp.lpSum(a(p, l) * x[p] for p in P)
        if y is not None and l in USES[OFFER_TRIP]:
            used += y
        model += (used <= capacity[l], f"capacity_{label(l)}")

    # Forecast demand: no fare of a trip sells more tickets than its forecast
    # demand. The demand is a constraint, not a bound of the variable, so that it has its own shadow
    # price.
    for p in P:
        model += (x[p] <= demand[p], f"demand_{label(p[0])}_{label(p[1])}")

    # The solver says whether it found an optimal solution: PuLP 3 returns the
    # status as a number and PuLP 4 as an object with a field status; 1 is
    # optimal in both
    result = model.solve(pulp.HiGHS(msg=False))
    if getattr(result, "status", result) != 1:
        return None

    # The constraints by name, with their shadow prices (pi): a method in
    # PuLP 4, a dict in PuLP 3
    constraints = model.constraints() if callable(model.constraints) else model.constraints
    if not isinstance(constraints, dict):
        constraints = {con.name: con for con in constraints}

    def clean(v):                    # no "-0.00" in the tables
        return 0.0 if abs(v) < 1e-9 else v

    # HiGHS returns the shadow prices of the minimisation it solves inside, so
    # in this maximisation their sign is the opposite of the change in revenue.
    # The minus sign gives them as the rise in revenue when the right-hand side
    # grows by one unit; Table 5 checks it by solving again.
    return (clean(pulp.value(model.objective)),
            {p: clean(x[p].value()) for p in P},
            {l: clean(-constraints[f"capacity_{label(l)}"].pi) for l in L},
            {p: clean(-constraints[f"demand_{label(p[0])}_{label(p[1])}"].pi) for p in P})


def seats_used(plan):
    return {l: sum(a(p, l) * plan[p] for p in P) for l in L}


# ---------------------------------------------------------------------------
# §3 and §5 The range in which a shadow price holds: re-solve the model with
# the right-hand side changed - the seats of the aircraft of a flight or the
# forecast demand of a fare of a trip - while the revenue changes by exactly
# the shadow price for each unit. The revenue is a concave piecewise linear
# function of each right-hand side, so the values that pass form an interval:
# the search doubles the step, then halves it. An end between two whole
# numbers is found by halving further, to a millionth.
# ---------------------------------------------------------------------------

def validity_range(side, key, capacity, demand, limit=1e6):
    """(lowest, highest) values of a right-hand side for which its shadow price
    holds. side = "seats": key is a flight and the right-hand side its seats;
    side = "demand": key is a fare of a trip and the right-hand side its forecast
    demand. None: no limit."""
    base_revenue, _, bid, demand_price = solve_model(capacity, demand)
    if side == "seats":
        start, price = capacity[key], bid[key]

        def resolve(value):
            return solve_model(with_value(capacity, key, value), demand)
    else:
        start, price = demand[key], demand_price[key]

        def resolve(value):
            return solve_model(capacity, with_value(demand, key, value))

    def holds(value):
        if value < 0:
            return False
        solution = resolve(value)
        return solution is not None and abs(solution[0] - (base_revenue + price * (value - start))) < 1e-6

    ends = []
    for direction in (-1, 1):
        good, step = 0, 1
        while step <= limit and holds(start + direction * step):
            good, step = step, 2 * step
        if step > limit:
            ends.append(None)
            continue
        bad = step
        while bad - good > 1e-6:
            middle = (good + bad) / 2 if bad - good <= 1 else (good + bad) // 2
            if holds(start + direction * middle):
                good = middle
            else:
                bad = middle
        end = start + direction * good
        ends.append(round(end) if abs(end - round(end)) < 1e-4 else end)
    return tuple(ends)


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


def num(value):
    return f"{value:,.2f}"


def limit_text(value):
    return "no limit" if value is None else num(value)


def grid(name, values):
    """A table with one row per trip and one column per fare."""
    print(f"{name:<12}" + "".join(f"{fare:>16}" for fare in FARES))
    for trip in TRIPS:
        print(f"{trip:<12}" + "".join(f"{values[trip, fare]:>16}" for fare in FARES))


# ---------------------------------------------------------------------------
# Main: print the results in the order of the document
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Stop with a clear message if the HiGHS solver is not installed
    if not pulp.HiGHS(msg=False).available():
        print("The HiGHS solver is not installed. Install it with:")
        print("    python -m pip install highspy     (Windows)")
        print("    python3 -m pip install highspy    (macOS and Linux)")
        sys.exit(1)

    # §1 Data
    title("§1 Flights, trips and fares")
    print("Table 1. Flights: seats of the aircraft")
    for l in L:
        print(f"{l:<12}{C[l]:>6} seats")
    print()
    print("Table 2. Trips: price (EUR/ticket) / forecast demand (tickets) of each fare")
    grid("Trip", {p: f"{r[p]} / {D[p]}" for p in P})

    # §2 The model and its optimal plan
    title("§2 Optimal plan of the model")
    revenue, plan, bid, demand_price = solve_model(C, D)
    print("Table 3. Optimal plan (tickets on sale)")
    grid("Trip", {p: num(plan[p]) for p in P})
    print(f"Revenue: {num(revenue)} EUR")
    print("Seats used: " + ", ".join(f"{l} {num(v)} of {C[l]}" for l, v in seats_used(plan).items()))
    print()
    print("Table 4. Binding constraints and slack")
    for l in L:
        gap = C[l] - seats_used(plan)[l]
        print(f"{'Seats of ' + l:<36}{'yes' if abs(gap) < 1e-6 else 'no':>8}{num(gap):>10}  seats")
    for p in P:
        gap = D[p] - plan[p]
        print(f"{'Demand of ' + p[0] + ' ' + p[1]:<36}{'yes' if abs(gap) < 1e-6 else 'no':>8}{num(gap):>10}  tickets")

    # §3 Bid prices
    title("§3 Bid prices")
    print("Table 5. Bid prices of the flights, checked by solving again with one seat more and one seat less")
    print(f"{'Flight':<12}{'Bid price (EUR/seat)':>22}{'One seat more (EUR)':>21}{'One seat less (EUR)':>21}")
    for l in L:
        changes = []
        for delta in (1, -1):
            changes.append(solve_model(with_value(C, l, C[l] + delta), D)[0] - revenue)
        print(f"{l:<12}{num(bid[l]):>22}{num(changes[0]):>21}{num(changes[1]):>21}")
    print()
    print("Table 6. Fares of the trips whose tickets change with one seat less and one seat more (tickets)")
    print(f"{'Flight':<12}{'Trip and fare':<26}{'One seat less':>15}{'Optimal plan':>14}{'One seat more':>15}"
          f"{'Change with one seat more (EUR)':>33}")
    for l in L:
        plans = [solve_model(with_value(C, l, C[l] + delta), D)[1] for delta in (-1, 0, 1)]
        less, base, more = plans
        changed = [p for p in P if abs(less[p] - base[p]) > 1e-6 or abs(more[p] - base[p]) > 1e-6]
        # First the tickets that take the extra seat, then those it displaces
        changed.sort(key=lambda p: -r[p] * (more[p] - base[p]))
        for p in changed:
            print(f"{l:<12}{p[0] + ' ' + p[1]:<26}{num(less[p]):>15}{num(base[p]):>14}{num(more[p]):>15}"
                  f"{num(r[p] * (more[p] - base[p])):>33}")
        print(f"{'':<12}{'Total with one seat more':<26}{'':>44}{num(sum(r[p] * (more[p] - base[p]) for p in changed)):>33}")
    print()
    print("Table 7. Bid price of the ticket of each fare of each trip and shadow price of its demand (EUR/ticket)")
    print(f"{'Trip':<10}{'Fare':<16}{'Price':>8}{'Bid price':>12}{'Shadow price of the demand':>28}")
    for p in P:
        product_bid = sum(a(p, l) * bid[l] for l in L)
        print(f"{p[0]:<10}{p[1]:<16}{num(r[p]):>8}{num(product_bid):>12}{num(demand_price[p]):>28}")
    print()
    print("Table 8. Seats of the aircraft for which the bid price of each flight holds (seats)")
    seat_ranges = {l: validity_range("seats", l, C, D) for l in L}
    for l in L:
        low, high = seat_ranges[l]
        print(f"{l:<12}{num(bid[l]):>10} EUR/seat{limit_text(low):>10}{limit_text(high):>10}")

    # §4 Offer of a tour operator
    title("§4 Offer of a tour operator")
    trip_bid = sum(bid[l] for l in USES[OFFER_TRIP])
    print(f"Bid price of a seat {OFFER_TRIP}: {num(trip_bid)} EUR/seat")
    print("Table 9. Offer of seats BCN-HEL on top of the forecast demand")
    print(f"{'Seats':>6}{'Price (EUR/seat)':>18}{'Estimate (EUR)':>16}{'Solving again (EUR)':>21}")
    for n, q in OFFERS:
        new_revenue = solve_model(C, D, offer=(n, q))[0]
        print(f"{n:>6}{num(q):>18}{num(n * (q - trip_bid)):>16}{num(new_revenue - revenue):>21}")

    # §5 Change in the forecast demand of a fare
    title("§5 Change in the forecast demand of a fare")
    print("Table 10. Shadow price of the demand of each fare of each trip and the demand for which it holds")
    print(f"{'Trip':<10}{'Fare':<16}{'Demand':>9}{'Shadow price (EUR/ticket)':>27}{'Holds from':>12}{'to':>12}")
    for p in P:
        low, high = validity_range("demand", p, C, D)
        print(f"{p[0]:<10}{p[1]:<16}{num(D[p]):>9}{num(demand_price[p]):>27}{limit_text(low):>12}{limit_text(high):>12}")
    print()
    print(f"Table 11. Campaign: {CHANGE_PRODUCT[0]} {CHANGE_PRODUCT[1]} demand {num(D[CHANGE_PRODUCT])} "
          f"-> {num(CHANGE_DEMAND)} tickets, {num(CHANGE_COST)} EUR")
    new_revenue, new_plan, new_bid, _ = solve_model(C, with_value(D, CHANGE_PRODUCT, CHANGE_DEMAND))
    change = new_revenue - revenue
    estimate = demand_price[CHANGE_PRODUCT] * (CHANGE_DEMAND - D[CHANGE_PRODUCT])
    low, high = validity_range("demand", CHANGE_PRODUCT, C, D)
    print(f"Revenue: {num(new_revenue)} EUR, {num(change)} EUR. Estimate with the shadow price: {num(estimate)} EUR")
    print(f"Net result: {num(change - CHANGE_COST)} EUR; with the estimate, {num(estimate - CHANGE_COST)} EUR")
    print(f"The demand of {num(CHANGE_DEMAND)} tickets is "
          f"{'inside' if low <= CHANGE_DEMAND <= high else 'outside'} the range "
          f"({limit_text(low)} to {limit_text(high)} tickets)")
    print("Change in revenue with 1, 2, 3, 5 and 10 tickets more of demand (EUR): "
          + ", ".join(num(solve_model(C, with_value(D, CHANGE_PRODUCT, D[CHANGE_PRODUCT] + extra))[0] - revenue)
                      for extra in (1, 2, 3, 5, 10)))
    print("Fares of the trips whose tickets change (tickets)")
    print(f"{'Trip':<10}{'Fare':<16}{num(D[CHANGE_PRODUCT]) + ' of demand':>20}{num(CHANGE_DEMAND) + ' of demand':>20}")
    for p in P:
        if abs(new_plan[p] - plan[p]) > 1e-6:
            print(f"{p[0]:<10}{p[1]:<16}{num(plan[p]):>20}{num(new_plan[p]):>20}")
    print("Bid prices with the new demand: " + ", ".join(f"{l} {num(new_bid[l])} EUR/seat" for l in L))
