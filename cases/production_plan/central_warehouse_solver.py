# Production plan with a central warehouse (M2)
#
# This script reproduces every table of central_warehouse.md (same folder): the
# data of the plants, the warehouse and forecast 3 (Tables 1 to 3); that M1,
# with stock at the plants only, has no solution with forecast 3; the plan of
# M2 with forecast 3 (Table 5); and the shadow prices of the backorder balance
# and of the
# storage capacities (Tables 6 and 7).
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
#     Windows:          python central_warehouse_solver.py
#     macOS and Linux:  python3 central_warehouse_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# §3 Data (Tables 1 to 3). Invented (2026)
# ---------------------------------------------------------------------------

F = ["Plant 1", "Plant 2", "Plant 3"]                 # assembly plants
T = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]        # months

# From production_plan.md (M0): unit assembly cost c[f] (EUR/bike) and
# capacity K[f][t] (bikes/month, the same every month)
c = {"Plant 1": 310, "Plant 2": 340, "Plant 3": 390}
K = {f: {t: cap for t in T} for f, cap in {"Plant 1": 250, "Plant 2": 200, "Plant 3": 150}.items()}

# From plant_stock.md (M1): holding cost c_h[f] (EUR/(bike*month)), stock at
# the end of December h_0[f] and required ending stock h_end[f]
# (bikes)
c_h = {"Plant 1": 5, "Plant 2": 6, "Plant 3": 7}
h_0 = {"Plant 1": 20, "Plant 2": 10, "Plant 3": 0}
h_end = dict(h_0)

# New in M2: storage capacity of the plants K_h[f] (bikes); holding cost
# c_h_w (EUR/(bike*month)) and storage capacity K_h_w (bikes) of the warehouse,
# its stock at the end of December h_w_0 and required ending stock h_w_end
# (bikes); backorder cost c_b (EUR/(bike*month)), backorders at the end of
# December b_0 and maximum backorders at the end of the horizon b_max (bikes)
K_h = {"Plant 1": 40, "Plant 2": 30, "Plant 3": 20}
c_h_w, K_h_w, h_w_0, h_w_end = 8, 150, 0, 0
c_b, b_0, b_max = 60, 0, 0

# Forecast 3: the orders that the warehouse receives (bikes/month)
d = dict(zip(T, [380, 900, 420, 440, 430, 230]))


# ---------------------------------------------------------------------------
# §4 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(m1=False):
    """Solve M2 with forecast 3. Returns (cost, values of each kind of variable,
    shadow prices of the backorder balance, of the storage at the plants and of the storage
    at the warehouse), or None if it has no solution. With m1=True, the model
    of M1 written with the variables of M2: no warehouse (it cannot hold stock),
    no backorders and no storage capacity at the plants."""
    model = pulp.LpProblem("central_warehouse", pulp.LpMinimize)

    def name(f, t):
        return f"{f.replace(' ', '')}_{t}"

    # p[f, t] = bikes assembled, x[f, t] = bikes shipped from plant f to the
    # warehouse in month t (bikes/month); h[f, t] = bikes in stock at plant f
    # at the end of month t (bikes)
    p = {(f, t): model.add_variable(f"p_{name(f, t)}", lowBound=0) for f in F for t in T}
    x = {(f, t): model.add_variable(f"x_{name(f, t)}", lowBound=0) for f in F for t in T}
    h = {(f, t): model.add_variable(f"h_{name(f, t)}", lowBound=0) for f in F for t in T}
    # h_w[t] = bikes in stock at the warehouse at the end of month t (bikes);
    # s[t] = deliveries in month t; b[t] = backorders at the end of month t
    h_w = {t: model.add_variable(f"h_w_{t}", lowBound=0) for t in T}
    s = {t: model.add_variable(f"s_{t}", lowBound=0) for t in T}
    b = {t: model.add_variable(f"b_{t}", lowBound=0) for t in T}

    # Minimise the assembly, holding and backorder cost
    model += (pulp.lpSum(c[f] * p[f, t] + c_h[f] * h[f, t] for f in F for t in T)
              + pulp.lpSum(c_h_w * h_w[t] + c_b * b[t] for t in T))

    for f in F:
        for i, t in enumerate(T):
            before = h_0[f] if i == 0 else h[f, T[i - 1]]
            # Stock balance at the plant
            model += (before + p[f, t] == x[f, t] + h[f, t], f"balance_{name(f, t)}")
            # Shipment limit at the plant: at most what it held at the start of
            # the month plus what it assembles
            model += (x[f, t] <= before + p[f, t], f"shipment_limit_{name(f, t)}")
            # Assembly capacity and storage capacity of the plant
            model += (p[f, t] <= K[f][t], f"capacity_{name(f, t)}")
            if not m1:
                model += (h[f, t] <= K_h[f], f"storage_{name(f, t)}")
        # Final stock at the plant
        model += (h[f, T[-1]] >= h_end[f], f"final_stock_{f.replace(' ', '')}")

    for i, t in enumerate(T):
        stock_before = h_w_0 if i == 0 else h_w[T[i - 1]]
        owed_before = b_0 if i == 0 else b[T[i - 1]]
        arriving = pulp.lpSum(x[f, t] for f in F)
        # Stock balance at the warehouse
        model += (stock_before + arriving == s[t] + h_w[t], f"warehouse_balance_{t}")
        # Shipment limit at the warehouse: it delivers at most what it held at the
        # start of the month plus what arrives
        model += (s[t] <= stock_before + arriving, f"shipment_limit_warehouse_{t}")
        # Backorder balance, written with the demand on the right so that
        # its shadow price is what one more order costs
        model += (s[t] + b[t] - owed_before == d[t], f"orders_{t}")
        # Storage capacity of the warehouse (none in M1)
        model += (h_w[t] <= (0 if m1 else K_h_w), f"warehouse_storage_{t}")
        if m1:
            model += (b[t] <= 0, f"no_backorders_{t}")
    # No backorders at the end of the horizon; required ending stock at the
    # warehouse
    model += (b[T[-1]] <= b_max, "backorders_at_the_end")
    model += (h_w[T[-1]] >= h_w_end, "final_stock_warehouse")

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

    values = {kind: {key: clean(var.value()) for key, var in variables.items()}
              for kind, variables in (("p", p), ("x", x), ("h", h), ("h_w", h_w), ("s", s), ("b", b))}
    if m1:
        return pulp.value(model.objective), values, None, None, None
    return (pulp.value(model.objective), values,
            {t: clean(constraints[f"orders_{t}"].pi) for t in T},
            {(f, t): clean(constraints[f"storage_{name(f, t)}"].pi) for f in F for t in T},
            {t: clean(constraints[f"warehouse_storage_{t}"].pi) for t in T})


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


def by_month(name, values):
    print(f"{name:<40}" + "".join(f"{v:>9.2f}" for v in values))


def header():
    print(f"{'':<40}" + "".join(f"{t:>9}" for t in T))


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
    title("§3 Data of the plants and the warehouse, forecast 3")
    print("Table 1. Plants")
    print(f"{'Plant':<10}{'c':>6}{'K':>6}{'c_h':>6}{'K_h':>6}{'h_0':>6}{'h_end':>7}")
    for f in F:
        print(f"{f:<10}{c[f]:>6}{K[f]['Jan']:>6}{c_h[f]:>6}{K_h[f]:>6}{h_0[f]:>6}{h_end[f]:>7}")
    print()
    print("Table 2. Central warehouse and backorders")
    print(f"c_h_w = {c_h_w} EUR/(bike*month), K_h_w = {K_h_w} bikes, h_w_0 = {h_w_0} bikes,"
          f" h_w_end = {h_w_end} bikes")
    print(f"c_b = {c_b} EUR/(bike*month), b_0 = {b_0} bikes, b_max = {b_max} bikes")
    print()
    print("Table 3. Forecast 3 and the capacity of the plants (bikes)")
    header()
    by_month("Orders, forecast 3", [d[t] for t in T])
    by_month("Capacity of the three plants", [sum(K[f][t] for f in F) for t in T])
    cum_d, cum_k = 0, 0
    rows_d, rows_k = [], []
    for t in T:
        cum_d += d[t]
        cum_k += sum(K[f][t] for f in F)
        rows_d.append(cum_d)
        rows_k.append(cum_k)
    by_month("Cumulative orders", rows_d)
    by_month("Cumulative capacity", rows_k)
    print(f"Stock at the plants at the end of December: {sum(h_0.values())} bikes")
    print(f"M1 (stock at the plants only) has a solution: {'yes' if solve_model(m1=True) else 'no'}")

    # §6.1 Plan of M2 with forecast 3
    title("§6.1 Optimal plan under forecast 3")
    cost, v, orders_price, storage_price, warehouse_price = solve_model()
    print("Table 5. Optimal plan (bikes)")
    header()
    for label, kind in (("Assembled", "p"), ("Shipped to the warehouse", "x"), ("Stock", "h")):
        for f in F:
            by_month(f"{label}, {f.lower()}", [v[kind][f, t] for t in T])
    by_month("Stock at the warehouse", [v["h_w"][t] for t in T])
    by_month("Deliveries of the warehouse", [v["s"][t] for t in T])
    by_month("Backorders at the end of the month", [v["b"][t] for t in T])
    print(f"Cost: {cost:.2f} EUR")
    print()
    print("Table 6. Shadow prices of the backorder balance (EUR/bike)")
    header()
    by_month("Backorder balance", [orders_price[t] for t in T])
    print()
    print("Table 7. Shadow prices of the storage capacities (EUR/bike)")
    header()
    for f in F:
        by_month(f"Storage capacity, {f.lower()}", [storage_price[f, t] for t in T])
    by_month("Storage capacity, warehouse", [warehouse_price[t] for t in T])
