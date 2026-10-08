# Production plan - how many bikes each plant assembles each month
#
# This script reproduces every table of production_plan.md (same folder): the
# reduced version with two plants and one month, its vertices, its optimum and
# its shadow prices with the ranges in which they hold (Tables 3 and 4); the
# plan of the full case with forecast 1, its shadow prices and reduced costs
# (Tables 5 and 6); and forecast 2, for which the model has no solution
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
#     Windows:          python production_plan_solver.py
#     macOS and Linux:  python3 production_plan_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# §1 Data (Tables 1 and 2). Invented (2026)
# ---------------------------------------------------------------------------

F = ["Plant 1", "Plant 2", "Plant 3"]                 # assembly plants
T = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]        # months

# Unit assembly cost c[f] (EUR/bike), Table 1
c = {"Plant 1": 310, "Plant 2": 340, "Plant 3": 390}

# Capacity K[f][t] (bikes/month), Table 1: the same every month
K = {f: {t: cap for t in T} for f, cap in {"Plant 1": 250, "Plant 2": 200, "Plant 3": 150}.items()}

# Demand d[t] of each forecast (bikes/month), Table 2
FORECASTS = {
    "Forecast 1": dict(zip(T, [380, 330, 420, 440, 430, 230])),
    "Forecast 2": dict(zip(T, [380, 330, 420, 650, 620, 230])),
}


# ---------------------------------------------------------------------------
# §2 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(plants, months, demand, capacity):
    """Solve the model. Returns (cost, plan, shadow prices of the demand, shadow
    prices of the capacities, reduced costs), or None if it has no solution."""
    model = pulp.LpProblem("production_plan", pulp.LpMinimize)

    # p[f, t] = bikes assembled in plant f in month t (continuous, >= 0)
    p = {(f, t): model.add_variable(f"p_{f.replace(' ', '')}_{t}", lowBound=0)
         for f in plants for t in months}

    # Minimise the assembly cost
    model += pulp.lpSum(c[f] * p[f, t] for f in plants for t in months)

    # The demand of each month is assembled that month
    for t in months:
        model += (pulp.lpSum(p[f, t] for f in plants) >= demand[t], f"demand_{t}")

    # No plant assembles more than its capacity. The capacities are
    # constraints, not bounds of the variables, so that each one has its own
    # shadow price.
    for f in plants:
        for t in months:
            model += (p[f, t] <= capacity[f][t], f"capacity_{f.replace(' ', '')}_{t}")

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

    return (pulp.value(model.objective),
            {key: clean(var.value()) for key, var in p.items()},
            {t: clean(constraints[f"demand_{t}"].pi) for t in months},
            {(f, t): clean(constraints[f"capacity_{f.replace(' ', '')}_{t}"].pi)
             for f in plants for t in months},
            {key: clean(var.dj) for key, var in p.items()})


# ---------------------------------------------------------------------------
# §3 The range in which a shadow price holds: re-solve the model with the
# right-hand side changed, one bike at a time, while the cost changes by
# exactly the shadow price for each bike. The cost is a convex piecewise
# linear function of the right-hand side, so the values that pass form an
# interval: the search doubles the step, then halves it.
# ---------------------------------------------------------------------------

def validity_range(plants, months, demand, capacity, kind, key, limit=1e6):
    """(lowest, highest) value of a demand (key t) or a capacity (key (f, t))
    for which its shadow price holds. None: no limit."""
    base_cost, _, demand_price, capacity_price, _ = solve_model(plants, months, demand, capacity)
    if kind == "demand":
        rhs, price = demand[key], demand_price[key]
    else:
        rhs, price = capacity[key[0]][key[1]], capacity_price[key]

    def holds(value):
        if value < 0:
            return False
        new_demand, new_capacity = dict(demand), {f: dict(capacity[f]) for f in capacity}
        if kind == "demand":
            new_demand[key] = value
        else:
            new_capacity[key[0]][key[1]] = value
        solution = solve_model(plants, months, new_demand, new_capacity)
        return solution is not None and abs(solution[0] - (base_cost + price * (value - rhs))) < 1e-6

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
    return tuple(ends)


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


def by_month(name, values):
    print(f"{name:<34}" + "".join(f"{v:>9.2f}" for v in values))


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

    # §3 Reduced version: plants 1 and 2, January
    title("§3 Reduced version: plants 1 and 2, January")
    plants, months = ["Plant 1", "Plant 2"], ["Jan"]
    demand = {"Jan": FORECASTS["Forecast 1"]["Jan"]}
    capacity = {f: dict(K[f]) for f in plants}
    k1, k2, d1 = capacity["Plant 1"]["Jan"], capacity["Plant 2"]["Jan"], demand["Jan"]

    # The feasible region is the triangle p1 <= k1, p2 <= k2, p1 + p2 >= d1
    print("Table 3. Vertices of the feasible region")
    print(f"{'p1 (bikes)':>12}{'p2 (bikes)':>12}{'Cost (EUR)':>14}")
    for p1, p2 in sorted([(k1, d1 - k1), (k1, k2), (d1 - k2, k2)]):
        print(f"{p1:>12.2f}{p2:>12.2f}{c['Plant 1'] * p1 + c['Plant 2'] * p2:>14.2f}")

    cost, plan, demand_price, capacity_price, _ = solve_model(plants, months, demand, capacity)
    print(f"Optimum: p1 = {plan['Plant 1', 'Jan']:.2f}, p2 = {plan['Plant 2', 'Jan']:.2f},"
          f" cost {cost:.2f} EUR")
    print()
    print("Table 4. Shadow prices and the ranges in which they hold")
    print(f"{'Constraint':<22}{'Right-hand side':>17}{'Shadow price (EUR/bike)':>25}{'Holds from':>12}{'to':>8}")
    for name, kind, key, rhs, price in (
            ("Capacity of plant 1", "capacity", ("Plant 1", "Jan"), k1, capacity_price["Plant 1", "Jan"]),
            ("Capacity of plant 2", "capacity", ("Plant 2", "Jan"), k2, capacity_price["Plant 2", "Jan"]),
            ("Demand", "demand", "Jan", d1, demand_price["Jan"])):
        low, high = validity_range(plants, months, demand, capacity, kind, key)
        low_text = "-" if low is None else f"{low:.2f}"
        high_text = "no limit" if high is None else f"{high:.2f}"
        print(f"{name:<22}{rhs:>17.2f}{price:>25.2f}{low_text:>12}{high_text:>10}")
    print(f"Spare capacity of plant 2: {k2 - plan['Plant 2', 'Jan']:.2f} bikes")

    # §4 Full case, forecast 1
    title("§4 Full case, forecast 1")
    cost, plan, demand_price, capacity_price, reduced = solve_model(F, T, FORECASTS["Forecast 1"], K)
    print("Table 5. Optimal plan (bikes/month)")
    print(f"{'':<34}" + "".join(f"{t:>9}" for t in T))
    for f in F:
        by_month(f, [plan[f, t] for t in T])
    print(f"Cost: {cost:.2f} EUR")
    print()
    print("Table 6. Shadow prices and reduced costs (EUR/bike)")
    print(f"{'':<34}" + "".join(f"{t:>9}" for t in T))
    by_month("Shadow price of the demand", [demand_price[t] for t in T])
    by_month("Shadow price of capacity, plant 1", [capacity_price["Plant 1", t] for t in T])
    for f in F:
        by_month(f"Reduced cost, {f.lower()}", [reduced[f, t] for t in T])

    # §5 Full case, forecast 2
    title("§5 Full case, forecast 2")
    demand = FORECASTS["Forecast 2"]
    solution = solve_model(F, T, demand, K)
    print(f"The model has a solution: {'yes' if solution else 'no'}")
    total = {t: sum(K[f][t] for f in F) for t in T}
    print()
    print("Table 7. Capacity and demand, month by month and cumulative (bikes)")
    print(f"{'':<22}" + "".join(f"{t:>8}" for t in T))
    print(f"{'Demand':<22}" + "".join(f"{demand[t]:>8}" for t in T))
    print(f"{'Capacity':<22}" + "".join(f"{total[t]:>8}" for t in T))
    print(f"{'Spare capacity':<22}" + "".join(f"{total[t] - demand[t]:>8}" for t in T))
    cum_d = cum_k = 0
    row_d, row_k = [], []
    for t in T:
        cum_d += demand[t]
        cum_k += total[t]
        row_d.append(cum_d)
        row_k.append(cum_k)
    print(f"{'Cumulative demand':<22}" + "".join(f"{v:>8}" for v in row_d))
    print(f"{'Cumulative capacity':<22}" + "".join(f"{v:>8}" for v in row_k))
    short = {t: demand[t] - total[t] for t in T if demand[t] > total[t]}
    print("Capacity short: " + ", ".join(f"{t} {v} bikes" for t, v in short.items()))
    free = [t for t in T[:T.index(next(iter(short)))]]
    print(f"Spare capacity before {next(iter(short))}: "
          + ", ".join(f"{t} {total[t] - demand[t]}" for t in free)
          + f" ({sum(total[t] - demand[t] for t in free)} in all)")
    never_below = all(k >= dd for k, dd in zip(row_k, row_d))
    print(f"Cumulative capacity never below cumulative demand: {'yes' if never_below else 'no'}")
