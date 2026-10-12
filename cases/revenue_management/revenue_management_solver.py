# Revenue management - how many tickets of each product an airline puts on
# sale on two connected flights
#
# This script reproduces every table of revenue_management.md (same folder):
# the flights and the products (Tables 1 and 2), the plan of the rule
# "highest fare first" (Table 3), the optimal plan against the rule (Table 4),
# the binding constraints and their slack (Table 5), the bid prices of the
# flights checked by solving again (Table 6), the bid prices of the products
# and the shadow prices of the demand (Table 7), the ranges of the bid prices
# (Table 8), an offer of a tour operator (Table 9) and two other aircraft for
# the second flight (Table 10).
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

# Flights and their capacity C[l] (seats)
L = ["BCN->RIX", "RIX->HEL"]
C = {"BCN->RIX": 220, "RIX->HEL": 140}

# Trips and the flights each one uses: a BCN-HEL ticket needs a seat on both
TRIPS = ["BCN-RIX", "RIX-HEL", "BCN-HEL"]
USES = {"BCN-RIX": ["BCN->RIX"], "RIX-HEL": ["RIX->HEL"], "BCN-HEL": ["BCN->RIX", "RIX->HEL"]}

# Fares and the seats one ticket uses on each flight of its trip: a Business
# ticket leaves the middle seat free
FARES = ["Business", "Economy FLEX", "Economy BASIC"]
SEATS = {"Business": 1.5, "Economy FLEX": 1, "Economy BASIC": 1}

# Products p = (trip, fare): price r[p] of a one-way ticket (EUR/ticket) and
# forecast demand D[p] (tickets)
P = [(trip, fare) for trip in TRIPS for fare in FARES]
r = dict(zip(P, [420, 180, 75,
                 200, 100, 45,
                 520, 230, 110]))
D = dict(zip(P, [16, 60, 160,
                 6, 40, 60,
                 6, 20, 80]))

# Offer of a tour operator (§7): seats BCN-HEL on top of the forecast demand
OFFER_TRIP = "BCN-HEL"
OFFERS = [(10, 100), (10, 120), (1, 120), (2, 120), (3, 120)]     # (seats, EUR/seat)

# Other aircraft for RIX->HEL (§8): (seats, operating cost against the
# 140-seat aircraft in EUR; negative: a saving)
OTHER_AIRCRAFT = [(180, 1200), (120, -800)]


def a(p, l):
    """Seats one ticket of product p uses on flight l: 0 if its trip does not use l."""
    trip, fare = p
    return SEATS[fare] if l in USES[trip] else 0


def label(text):
    """A name PuLP accepts: letters, digits and underscores."""
    return "".join(ch if ch.isalnum() else "_" for ch in text)


# ---------------------------------------------------------------------------
# §2 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(capacity, demand, offer=None):
    """Solve the model. Returns (revenue, plan, bid prices of the flights, shadow
    prices of the demand), or None if it has no solution. offer = (n, q): n seats
    of OFFER_TRIP at q EUR/seat, forced into the plan."""
    model = pulp.LpProblem("revenue_management", pulp.LpMaximize)

    # x[p] = tickets of product p put on sale (continuous, >= 0)
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

    # The seats used on each flight do not exceed its capacity
    for l in L:
        used = pulp.lpSum(a(p, l) * x[p] for p in P)
        if y is not None and l in USES[OFFER_TRIP]:
            used += y
        model += (used <= capacity[l], f"capacity_{label(l)}")

    # No product sells more tickets than its forecast demand. The demand is a
    # constraint, not a bound of the variable, so that it has its own shadow
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
    # grows by one unit; Table 6 checks it by solving again.
    return (clean(pulp.value(model.objective)),
            {p: clean(x[p].value()) for p in P},
            {l: clean(-constraints[f"capacity_{label(l)}"].pi) for l in L},
            {p: clean(-constraints[f"demand_{label(p[0])}_{label(p[1])}"].pi) for p in P})


def seats_used(plan):
    return {l: sum(a(p, l) * plan[p] for p in P) for l in L}


# ---------------------------------------------------------------------------
# §3 The rule "highest fare first", without a solver: the products in
# decreasing order of price, each up to its demand or until a flight it uses
# is full
# ---------------------------------------------------------------------------

def highest_fare_first(capacity, demand):
    left = dict(capacity)
    plan = {}
    for p in sorted(P, key=lambda p: -r[p]):          # the nine prices are all different
        flights = [l for l in L if a(p, l) > 0]
        plan[p] = min([demand[p]] + [left[l] / a(p, l) for l in flights])
        for l in flights:
            left[l] -= a(p, l) * plan[p]
    return plan


# ---------------------------------------------------------------------------
# §6 The range in which a bid price holds: re-solve the model with the
# capacity of the flight changed, one seat at a time, while the revenue
# changes by exactly the bid price for each seat. The revenue is a concave
# piecewise linear function of the capacity, so the values that pass form an
# interval: the search doubles the step, then halves it. An end between two
# whole numbers is found by halving further, to a millionth.
# ---------------------------------------------------------------------------

def validity_range(flight, capacity, demand, limit=1e6):
    """(lowest, highest) capacity of a flight for which its bid price holds. None: no limit."""
    base_revenue, _, bid, _ = solve_model(capacity, demand)
    start, price = capacity[flight], bid[flight]

    def holds(value):
        if value < 0:
            return False
        new_capacity = dict(capacity)
        new_capacity[flight] = value
        solution = solve_model(new_capacity, demand)
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
    title("§1 Flights and products")
    print("Table 1. Flights")
    for l in L:
        print(f"{l:<12}{C[l]:>6} seats")
    print()
    print("Table 2. Products: price (EUR/ticket) / forecast demand (tickets)")
    grid("Trip", {p: f"{r[p]} / {D[p]}" for p in P})

    # §3 The rule
    title("§3 The rule 'highest fare first'")
    rule = highest_fare_first(C, D)
    rule_revenue = sum(r[p] * rule[p] for p in P)
    print("Table 3. Plan of the rule (tickets on sale)")
    grid("Trip", {p: num(rule[p]) for p in P})
    print(f"Revenue of the rule: {num(rule_revenue)} EUR")
    print("Seats used: " + ", ".join(f"{l} {num(v)} of {C[l]}" for l, v in seats_used(rule).items()))

    # §4 Optimal plan
    title("§4 Optimal plan, against the rule")
    revenue, plan, bid, demand_price = solve_model(C, D)
    print("Table 4. Plan of the rule and optimal plan (tickets), and the difference")
    print(f"{'Trip':<10}{'Fare':<16}{'Rule':>10}{'Model':>10}{'Rule - model':>14}{'(EUR)':>12}")
    for p in P:
        diff = rule[p] - plan[p]
        print(f"{p[0]:<10}{p[1]:<16}{num(rule[p]):>10}{num(plan[p]):>10}{num(diff):>14}{num(r[p] * diff):>12}")
    print(f"Revenue: model {num(revenue)} EUR, rule {num(rule_revenue)} EUR. The rule loses "
          f"{num(revenue - rule_revenue)} EUR, {(revenue - rule_revenue) / revenue * 100:.1f} % of the optimal revenue")
    print("Seats used: " + ", ".join(f"{l} {num(v)} of {C[l]}" for l, v in seats_used(plan).items()))
    print()
    print("Table 5. Binding constraints and slack")
    for l in L:
        gap = C[l] - seats_used(plan)[l]
        print(f"{'Capacity of ' + l:<36}{'yes' if abs(gap) < 1e-6 else 'no':>8}{num(gap):>10}  seats")
    for p in P:
        gap = D[p] - plan[p]
        print(f"{'Demand of ' + p[0] + ' ' + p[1]:<36}{'yes' if abs(gap) < 1e-6 else 'no':>8}{num(gap):>10}  tickets")

    # §5 Bid prices
    title("§5 Bid prices")
    print("Table 6. Bid prices of the flights, checked by solving again with one seat more and one seat less")
    print(f"{'Flight':<12}{'Bid price (EUR/seat)':>22}{'One seat more (EUR)':>21}{'One seat less (EUR)':>21}")
    for l in L:
        changes = []
        for delta in (1, -1):
            new_capacity = dict(C)
            new_capacity[l] += delta
            changes.append(solve_model(new_capacity, D)[0] - revenue)
        print(f"{l:<12}{num(bid[l]):>22}{num(changes[0]):>21}{num(changes[1]):>21}")
    print()
    print("Table 7. Bid price of each product and shadow price of its demand (EUR/ticket)")
    print(f"{'Trip':<10}{'Fare':<16}{'Price':>8}{'Bid price':>12}{'Shadow price of the demand':>28}")
    for p in P:
        product_bid = sum(a(p, l) * bid[l] for l in L)
        print(f"{p[0]:<10}{p[1]:<16}{num(r[p]):>8}{num(product_bid):>12}{num(demand_price[p]):>28}")

    # §6 Ranges
    title("§6 Ranges of the bid prices")
    print("Table 8. Capacities for which the bid price of each flight holds (seats)")
    ranges = {l: validity_range(l, C, D) for l in L}
    for l in L:
        low, high = ranges[l]
        print(f"{l:<12}{num(bid[l]):>10} EUR/seat{num(low):>10}{'no limit' if high is None else num(high):>10}")

    # §7 Offer of a tour operator
    title("§7 Offer of a tour operator")
    trip_bid = sum(bid[l] for l in USES[OFFER_TRIP])
    print(f"Bid price of a seat {OFFER_TRIP}: {num(trip_bid)} EUR/seat")
    print("Table 9. Offer of seats BCN-HEL on top of the forecast demand")
    print(f"{'Seats':>6}{'Price (EUR/seat)':>18}{'Estimate (EUR)':>16}{'Solving again (EUR)':>21}")
    for n, q in OFFERS:
        new_revenue = solve_model(C, D, offer=(n, q))[0]
        print(f"{n:>6}{num(q):>18}{num(n * (q - trip_bid)):>16}{num(new_revenue - revenue):>21}")

    # §8 Another aircraft on RIX->HEL
    title("§8 Another aircraft on RIX->HEL")
    flight = "RIX->HEL"
    low, high = ranges[flight]
    print("Table 10. Another aircraft on RIX->HEL, against 140 seats")
    print(f"{'Seats':>6}{'Revenue (EUR)':>15}{'Change (EUR)':>14}{'Estimate (EUR)':>16}{'Inside range':>14}"
          f"{'Cost change (EUR)':>19}{'Net (EUR)':>12}")
    for seats, cost in OTHER_AIRCRAFT:
        new_capacity = dict(C)
        new_capacity[flight] = seats
        new_revenue, new_plan, _, _ = solve_model(new_capacity, D)
        change = new_revenue - revenue
        inside = low <= seats <= high
        print(f"{seats:>6}{num(new_revenue):>15}{num(change):>14}{num(bid[flight] * (seats - C[flight])):>16}"
              f"{'yes' if inside else 'no':>14}{num(cost):>19}{num(change - cost):>12}")
        print("       changed: " + ", ".join(f"{p[0]} {p[1]} {num(plan[p])} -> {num(new_plan[p])}"
                                           for p in P if abs(new_plan[p] - plan[p]) > 1e-6))
