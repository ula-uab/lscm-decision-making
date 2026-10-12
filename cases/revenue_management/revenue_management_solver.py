# Revenue management - how many tickets of each fare an airline puts on sale
#
# This script reproduces every table of revenue_management.md (same folder):
# the fares (Table 1), the optimal plan (Table 2), the binding constraints and
# their slack (Table 3), the shadow prices checked by solving again (Table 4),
# the ranges in which they hold (Table 5), the pieces of the revenue curve
# against the capacity of the cabin (Table 6) and two other capacities
# (Table 7).
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
# §1 Data (Table 1). Invented (2026)
# ---------------------------------------------------------------------------

F = ["Business", "Economy FLEX", "Economy BASIC"]       # fares

# Price r[f] of a one-way ticket (EUR/ticket)
r = {"Business": 420, "Economy FLEX": 180, "Economy BASIC": 75}

# Seats a[f] used by one ticket: a Business ticket leaves the middle seat free
a = {"Business": 1.5, "Economy FLEX": 1, "Economy BASIC": 1}

# Forecast demand D[f] (tickets)
D = {"Business": 24, "Economy FLEX": 120, "Economy BASIC": 140}

# Capacity of the cabin (seats): Airbus A321, flexible cabin
C = 220

# Capacities drawn in the curve of revenue against capacity (seats), §6
CURVE = (0, 320)

# Other capacities compared with 220 seats (seats), §7
OTHER = [180, 150]

# A constraint is named by a key: "capacity", or the name of a fare for its demand
KEYS = ["capacity"] + F


# ---------------------------------------------------------------------------
# §2 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(capacity, demand):
    """Solve the model. Returns (revenue, plan, shadow prices), with the shadow
    prices by key: "capacity" (the bid price, EUR/seat) and each fare (EUR/ticket)."""
    model = pulp.LpProblem("revenue_management", pulp.LpMaximize)

    # x[f] = tickets of fare f put on sale (continuous, >= 0)
    x = {f: model.add_variable(f"x_{f.replace(' ', '_')}", lowBound=0) for f in F}

    # Maximise the revenue
    model += pulp.lpSum(r[f] * x[f] for f in F)

    # The tickets on sale fit in the cabin
    model += (pulp.lpSum(a[f] * x[f] for f in F) <= capacity, "capacity")

    # No fare sells more tickets than its forecast demand. The demand is a
    # constraint, not a bound of the variable, so that it has its own shadow
    # price.
    for f in F:
        model += (x[f] <= demand[f], f"demand_{f.replace(' ', '_')}")

    # The solver says whether it found an optimal solution: PuLP 3 returns the
    # status as a number and PuLP 4 as an object with a field status; 1 is
    # optimal in both
    result = model.solve(pulp.HiGHS(msg=False))
    if getattr(result, "status", result) != 1:
        raise RuntimeError("The solver did not find an optimal solution.")

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
    # grows by one unit; Table 4 checks it by solving again.
    prices = {"capacity": clean(-constraints["capacity"].pi)}
    for f in F:
        prices[f] = clean(-constraints[f"demand_{f.replace(' ', '_')}"].pi)
    return (clean(pulp.value(model.objective)),
            {f: clean(x[f].value()) for f in F},
            prices)


def changed(key, value, capacity, demand):
    """(capacity, demand) with the right-hand side of one constraint set to value."""
    if key == "capacity":
        return value, demand
    new_demand = dict(demand)
    new_demand[key] = value
    return capacity, new_demand


def right_hand_side(key, capacity, demand):
    return capacity if key == "capacity" else demand[key]


# ---------------------------------------------------------------------------
# §5 The range in which a shadow price holds: re-solve the model with the
# right-hand side changed, one unit at a time, while the revenue changes by
# exactly the shadow price for each unit. The revenue is a concave piecewise
# linear function of the right-hand side, so the values that pass form an
# interval: the search doubles the step, then halves it. An end between two
# whole numbers is found by halving further, to a millionth.
# ---------------------------------------------------------------------------

def validity_range(key, capacity, demand, limit=1e6):
    """(lowest, highest) value of a right-hand side for which its shadow price
    holds. None: no limit."""
    base_revenue, _, prices = solve_model(capacity, demand)
    rhs, price = right_hand_side(key, capacity, demand), prices[key]

    def holds(value):
        if value < 0:
            return False
        revenue = solve_model(*changed(key, value, capacity, demand))[0]
        return abs(revenue - (base_revenue + price * (value - rhs))) < 1e-6

    ends = []
    for direction in (-1, 1):
        good, step = 0, 1
        while step <= limit and holds(rhs + direction * step):
            good, step = step, 2 * step
        if step > limit:
            ends.append(None)
            continue
        bad = step
        while bad - good > 1e-6:
            middle = (good + bad) / 2 if bad - good <= 1 else (good + bad) // 2
            if holds(rhs + direction * middle):
                good = middle
            else:
                bad = middle
        end = rhs + direction * good
        ends.append(round(end) if abs(end - round(end)) < 1e-4 else end)
    return tuple(ends)


# ---------------------------------------------------------------------------
# §6 Revenue against capacity: solve for every whole capacity and join the
# capacities where the revenue grows by the same amount per seat
# ---------------------------------------------------------------------------

def segments(demand, low=CURVE[0], high=CURVE[1]):
    """[(from, to, slope)]: the straight pieces of the revenue curve (seats, EUR/seat)."""
    revenue = [solve_model(k, demand)[0] for k in range(low, high + 1)]
    pieces = []
    for k in range(low, high):
        slope = revenue[k + 1 - low] - revenue[k - low]
        if pieces and abs(pieces[-1][2] - slope) < 1e-6:
            pieces[-1][1] = k + 1
        else:
            pieces.append([k, k + 1, 0.0 if abs(slope) < 1e-6 else slope])
    return [tuple(p) for p in pieces]


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


def name(key):
    return "Capacity of the cabin" if key == "capacity" else f"Demand of {key}"


def unit(key):
    return "seats" if key == "capacity" else "tickets"


def num(value):
    return f"{value:,.2f}"


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
    title("§1 Fares of the flight")
    print(f"Table 1. Fares (capacity of the cabin: {C} seats)")
    print(f"{'Fare':<16}{'Price (EUR/ticket)':>20}{'Seats per ticket':>18}{'Demand (tickets)':>18}"
          f"{'Revenue per seat (EUR/seat)':>29}")
    for f in F:
        print(f"{f:<16}{num(r[f]):>20}{num(a[f]):>18}{D[f]:>18}{num(r[f] / a[f]):>29}")

    # §3 Optimal plan
    title("§3 Optimal plan and binding constraints")
    revenue, plan, prices = solve_model(C, D)
    seats = sum(a[f] * plan[f] for f in F)
    print("Table 2. Optimal plan")
    print(f"{'Fare':<16}{'Tickets on sale':>17}{'Seats used':>12}{'Revenue (EUR)':>15}")
    for f in F:
        print(f"{f:<16}{num(plan[f]):>17}{num(a[f] * plan[f]):>12}{num(r[f] * plan[f]):>15}")
    print(f"{'Total':<16}{num(sum(plan.values())):>17}{num(seats):>12}{num(revenue):>15}")
    print(f"Revenue: {num(revenue)} EUR")
    print()
    print("Table 3. Binding constraints and slack")
    print(f"{'Constraint':<28}{'Used':>10}{'Right-hand side':>17}{'Binding':>9}{'Slack':>10}")
    for key in KEYS:
        used = seats if key == "capacity" else plan[key]
        rhs = right_hand_side(key, C, D)
        gap = rhs - used
        print(f"{name(key):<28}{num(used):>10}{num(rhs):>17}{'yes' if abs(gap) < 1e-6 else 'no':>9}"
              f"{num(gap):>10}  {unit(key)}")

    # §4 Shadow prices, checked by solving again with one more unit
    title("§4 Shadow prices")
    print("Table 4. Shadow prices, checked by solving again with one more unit of the right-hand side")
    print(f"{'Constraint':<28}{'Shadow price (EUR/unit)':>25}{'Revenue with one more (EUR)':>29}"
          f"{'Change (EUR)':>14}")
    for key in KEYS:
        new_revenue = solve_model(*changed(key, right_hand_side(key, C, D) + 1, C, D))[0]
        print(f"{name(key):<28}{num(prices[key]):>25}{num(new_revenue):>29}{num(new_revenue - revenue):>14}")
    print(f"Bid price: {num(prices['capacity'])} EUR/seat")

    # §5 Ranges
    title("§5 Ranges of the shadow prices")
    print("Table 5. Values of the right-hand side for which each shadow price holds")
    print(f"{'Constraint':<28}{'Shadow price':>14}{'Holds from':>12}{'to':>12}")
    ranges = {key: validity_range(key, C, D) for key in KEYS}
    for key in KEYS:
        low, high = ranges[key]
        print(f"{name(key):<28}{num(prices[key]):>14}{num(low):>12}"
              f"{'no limit' if high is None else num(high):>12}  {unit(key)}")

    # §6 Revenue against capacity
    title("§6 Revenue against the capacity of the cabin")
    print(f"Table 6. Pieces of the revenue curve, from {CURVE[0]} to {CURVE[1]} seats")
    print(f"{'From (seats)':>13}{'To (seats)':>12}{'Slope (EUR/seat)':>18}")
    for start, end, slope in segments(D):
        print(f"{start:>13}{end:>12}{num(slope):>18}")

    # §7 Another capacity
    title("§7 Another aircraft")
    low, high = ranges["capacity"]
    print(f"Table 7. Plan and revenue with another capacity, against {C} seats")
    print(f"{'Seats':>6}{'Business':>10}{'FLEX':>8}{'BASIC':>8}{'Revenue (EUR)':>15}{'Loss (EUR)':>12}"
          f"{'Bid price estimate (EUR)':>26}{'Inside the range':>18}")
    for capacity in [C] + OTHER:
        new_revenue, new_plan, _ = solve_model(capacity, D)
        loss = revenue - new_revenue
        estimate = prices["capacity"] * (C - capacity)
        inside = low <= capacity <= high
        print(f"{capacity:>6}" + "".join(f"{num(new_plan[f]):>{w}}" for f, w in zip(F, (10, 8, 8)))
              + f"{num(new_revenue):>15}{num(loss):>12}{num(estimate):>26}{'yes' if inside else 'no':>18}")
