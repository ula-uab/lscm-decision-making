# Production plan with stock at the plants (M1)
#
# This script reproduces every table of plant_stock.md (same folder): the data
# of the plants and forecast 2 (Tables 1 and 2); the plan with forecast 2 and
# the required final stock, with the shadow prices of the demand (Tables 4
# and 5); the plan without the required final stock (Tables 5 and 6); and a plan from January to
# March followed by a plan from April to June, which has no solution (Table 7).
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
#     Windows:          python plant_stock_solver.py
#     macOS and Linux:  python3 plant_stock_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# §3 Data (Tables 1 and 2). Invented (2026)
# ---------------------------------------------------------------------------

F = ["Plant 1", "Plant 2", "Plant 3"]                 # assembly plants
T = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]        # months

# From production_plan.md (M0): unit assembly cost c[f] (EUR/bike) and
# capacity K[f][t] (bikes/month, the same every month)
c = {"Plant 1": 310, "Plant 2": 340, "Plant 3": 390}
K = {f: {t: cap for t in T} for f, cap in {"Plant 1": 250, "Plant 2": 200, "Plant 3": 150}.items()}

# Demand d[t] of forecast 2 (bikes/month), Table 2 of production_plan.md
d = dict(zip(T, [380, 330, 420, 650, 620, 230]))

# New in M1: holding cost c_h[f] (EUR/(bike*month)), initial stock h_0[f]
# (bikes), at the end of December, and required final stock h_end[f] (bikes),
# equal to the initial stock
c_h = {"Plant 1": 5, "Plant 2": 6, "Plant 3": 7}
h_0 = {"Plant 1": 20, "Plant 2": 10, "Plant 3": 0}
h_end = dict(h_0)


# ---------------------------------------------------------------------------
# §4 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(months, initial, final):
    """Solve the model over the months given, starting from the stock initial[f].
    final=None: no required final stock. Returns (cost, assembled, shipped, stock,
    shadow prices of the demand), or None if the model has no solution."""
    model = pulp.LpProblem("plant_stock", pulp.LpMinimize)

    def name(f, t):
        return f"{f.replace(' ', '')}_{t}"

    # p[f, t] = bikes assembled, x[f, t] = bikes shipped from plant f in month t
    # (bikes/month); h[f, t] = bikes in stock at plant f at the end of month t
    # (bikes). All continuous, >= 0
    p = {(f, t): model.add_variable(f"p_{name(f, t)}", lowBound=0) for f in F for t in months}
    x = {(f, t): model.add_variable(f"x_{name(f, t)}", lowBound=0) for f in F for t in months}
    h = {(f, t): model.add_variable(f"h_{name(f, t)}", lowBound=0) for f in F for t in months}

    # Minimise the assembly and holding cost
    model += pulp.lpSum(c[f] * p[f, t] + c_h[f] * h[f, t] for f in F for t in months)

    for f in F:
        for i, t in enumerate(months):
            before = initial[f] if i == 0 else h[f, months[i - 1]]
            # Stock balance: stock at the start of the month plus what is
            # assembled is what is shipped plus the stock at the end of the month
            model += (before + p[f, t] == x[f, t] + h[f, t], f"balance_{name(f, t)}")
            # Shipment limit: a plant ships at most what it held at the start of
            # the month plus what it assembles
            model += (x[f, t] <= before + p[f, t], f"shipment_limit_{name(f, t)}")
            # Capacity
            model += (p[f, t] <= K[f][t], f"capacity_{name(f, t)}")
        # Required final stock, only in the runs that require it
        if final is not None:
            model += (h[f, months[-1]] >= final[f], f"final_stock_{f.replace(' ', '')}")

    # Demand: the plants together ship at least the demand of each month
    for t in months:
        model += (pulp.lpSum(x[f, t] for f in F) >= d[t], f"demand_{t}")

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
            {key: clean(var.value()) for key, var in x.items()},
            {key: clean(var.value()) for key, var in h.items()},
            {t: clean(constraints[f"demand_{t}"].pi) for t in months})


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def eu(x, decimals=2):
    """A number in European format: point for thousands, comma for decimals."""
    return f"{x:,.{decimals}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def title(text):
    print()
    print(text)
    print("=" * len(text))


def by_month(name, values):
    print(f"{name:<34}" + "".join(f"{eu(v):>9}" for v in values))


def print_plan(months, assembled, shipped, stock):
    print(f"{'':<34}" + "".join(f"{t:>9}" for t in months))
    for label, values in (("Assembled", assembled), ("Shipped", shipped), ("Stock", stock)):
        for f in F:
            by_month(f"{label}, {f.lower()}", [values[f, t] for t in months])


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

    # §3 Data
    title("§3 Plant data and forecast 2")
    print("Table 1. Plants")
    print(f"{'Plant':<10}{'c (EUR/bike)':>14}{'K (bikes/month)':>17}{'c_h (EUR/(bike*month))':>24}"
          f"{'h_0 (bikes)':>13}{'h_end (bikes)':>15}")
    for f in F:
        print(f"{f:<10}{c[f]:>14}{K[f]['Jan']:>17}{c_h[f]:>24}{h_0[f]:>13}{h_end[f]:>15}")
    print()
    print("Table 2. Forecast 2 and the capacity of the plants (bikes/month)")
    print(f"{'':<34}" + "".join(f"{t:>9}" for t in T))
    by_month("Demand, forecast 2", [d[t] for t in T])
    by_month("Capacity of plants 1 and 2", [K["Plant 1"][t] + K["Plant 2"][t] for t in T])
    by_month("Capacity of the three plants", [sum(K[f][t] for f in F) for t in T])
    short = {t: d[t] - K["Plant 1"][t] - K["Plant 2"][t] for t in T
             if d[t] > K["Plant 1"][t] + K["Plant 2"][t]}
    print("Demand above the capacity of plants 1 and 2: " + "; ".join(f"{t} {eu(v, 0)} bikes" for t, v in short.items()))

    # §6.1 Plan with forecast 2 and the required final stock
    title("§6.1 Optimal plan with the required final stock")
    cost, assembled, shipped, stock, price_target = solve_model(T, h_0, h_end)
    print("Table 4. Optimal plan (bikes)")
    print_plan(T, assembled, shipped, stock)
    print(f"Cost: {eu(cost)} EUR")

    # §6.2 Without the required final stock
    title("§6.2 Optimal plan without the required final stock")
    cost_free, assembled_free, shipped_free, stock_free, price_free = solve_model(T, h_0, None)
    print(f"Cost: {eu(cost_free)} EUR")
    print()
    print("Table 5. Shadow prices of the demand (EUR/bike)")
    print(f"{'':<34}" + "".join(f"{t:>9}" for t in T))
    by_month("With the required final stock", [price_target[t] for t in T])
    by_month("Without the required final stock", [price_free[t] for t in T])
    print()
    print("Table 6. June with and without the required final stock (bikes)")
    print(f"{'':<34}{'with':>9}{'without':>9}")
    for f in F:
        print(f"{'Assembled, ' + f.lower():<34}{eu(assembled[f, 'Jun']):>9}{eu(assembled_free[f, 'Jun']):>9}")
    for f in F:
        print(f"{'Stock at the end, ' + f.lower():<34}{eu(stock[f, 'Jun']):>9}{eu(stock_free[f, 'Jun']):>9}")
    same = [t for t in T if t != "Jun"
            and all(assembled[f, t] == assembled_free[f, t] and shipped[f, t] == shipped_free[f, t]
                    and stock[f, t] == stock_free[f, t] for f in F)]
    print("Months with the same plan: " + ", ".join(same))

    # §6.3 A horizon from January to March, then from April to June
    title("§6.3 Planning horizon from January to March")
    first, later = T[:3], T[3:]
    cost_first, assembled_first, shipped_first, stock_first, _ = solve_model(first, h_0, h_end)
    print("Table 7. Optimal plan from January to March, with the required final stock (bikes)")
    print_plan(first, assembled_first, shipped_first, stock_first)
    print(f"Cost: {eu(cost_first)} EUR")
    left = {f: stock_first[f, "Mar"] for f in F}
    print()
    print("Stock at the end of March: " + "; ".join(f"{f} {eu(left[f])}" for f in F))
    solution = solve_model(later, left, h_end)
    print(f"The plan from April to June has a solution: {'yes' if solution else 'no'}")
    print(f"April: demand {eu(d['Apr'], 0)}; capacity {eu(sum(K[f]['Apr'] for f in F), 0)};"
          f" stock at the start {eu(sum(left.values()))}")
