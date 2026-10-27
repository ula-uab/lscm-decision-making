# Production plan with a distribution network (M3)
#
# This script reproduces every table of distribution_network.md (same folder):
# the nodes and the list of arcs of the network, the data of each node and
# forecast 4 (Tables 1 to 4); that M2, with the plants and the central warehouse
# only, has no solution with forecast 4; the plan of M3 with forecast 4 (Tables 6
# to 8); and the shadow prices of the capacities that are full (Table 9).
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
#     Windows:          python distribution_network_solver.py
#     macOS and Linux:  python3 distribution_network_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# §3 Data (Tables 1 to 4). Invented (2026), except the places and distances
# ---------------------------------------------------------------------------

T = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]        # months
F = ["Plant 1", "Plant 2", "Plant 3"]                 # assembly plants
CENTRAL, TERMINAL = "Central warehouse", "Rail terminal"
REGIONAL = ["Regional warehouse 1", "Regional warehouse 2"]
LOCAL = ["Local warehouse 1", "Local warehouse 2", "Local warehouse 3", "Local warehouse 4"]
NODES = F + [CENTRAL, TERMINAL] + REGIONAL + LOCAL

# Place of each node (Nominatim, OpenStreetMap, consulted on 23/10/2026)
PLACES = {"Plant 1": "Vitoria-Gasteiz", "Plant 2": "Pamplona", "Plant 3": "Castellón de la Plana",
          CENTRAL: "Zaragoza", TERMINAL: "Coslada", "Regional warehouse 1": "Barcelona",
          "Regional warehouse 2": "Getafe", "Local warehouse 1": "Girona", "Local warehouse 2": "Tarragona",
          "Local warehouse 3": "Valencia", "Local warehouse 4": "Seville"}

# From M0-M2: unit assembly cost c[f] (EUR/bike) and capacity K[f][t] (bikes/month)
c = {"Plant 1": 310, "Plant 2": 340, "Plant 3": 390}
K = {f: {t: cap for t in T} for f, cap in {"Plant 1": 250, "Plant 2": 200, "Plant 3": 150}.items()}

# Holding cost c_h[i] (EUR/(bike*month)), storage capacity K_h[i] (bikes), initial
# stock h_0[i] and required final stock h_end[i] (bikes) of
# every node. Plants and central warehouse: as in M2. Rail terminal: no stock
c_h = {"Plant 1": 5, "Plant 2": 6, "Plant 3": 7, CENTRAL: 8, TERMINAL: 0,
       "Regional warehouse 1": 9, "Regional warehouse 2": 10,
       "Local warehouse 1": 11, "Local warehouse 2": 12, "Local warehouse 3": 13, "Local warehouse 4": 14}
K_h = {"Plant 1": 40, "Plant 2": 30, "Plant 3": 20, CENTRAL: 150, TERMINAL: 0,
       "Regional warehouse 1": 60, "Regional warehouse 2": 60,
       "Local warehouse 1": 20, "Local warehouse 2": 20, "Local warehouse 3": 20, "Local warehouse 4": 20}
h_0 = {i: {"Plant 1": 20, "Plant 2": 10}.get(i, 0) for i in NODES}
h_end = dict(h_0)

# Node capacity K_n[i]: bikes the node can receive in a month
K_n = {"Regional warehouse 2": 280}

# Transport rate of each mode (EUR/(bike*km)), invented
RATE = {"Road": 0.010, "Rail": 0.006}

# The network as a list of arcs: origin, destination, mode, distance (km) and
# arc capacity (bikes/month). Distances: OSRM (road) and OpenRailRouting (rail),
# on OpenStreetMap data, consulted on 23/10/2026. The transport cost of an arc
# is its distance times the rate of its mode, rounded to the cent (EUR/bike)
NETWORK = [
    ("Plant 1", CENTRAL, "Road", 262.0, 300),
    ("Plant 2", CENTRAL, "Road", 181.7, 300),
    ("Plant 3", CENTRAL, "Road", 323.3, 300),
    ("Plant 3", "Regional warehouse 2", "Road", 427.2, 60),
    (CENTRAL, "Regional warehouse 1", "Road", 311.3, 600),
    (CENTRAL, TERMINAL, "Rail", 336.0, 400),
    (TERMINAL, "Regional warehouse 2", "Road", 27.5, 200),
    (CENTRAL, "Regional warehouse 2", "Road", 329.9, 150),
    ("Regional warehouse 1", "Local warehouse 1", "Road", 102.0, 300),
    ("Regional warehouse 1", "Local warehouse 2", "Road", 97.1, 300),
    ("Regional warehouse 1", "Local warehouse 3", "Road", 350.7, 300),
    ("Regional warehouse 2", "Local warehouse 3", "Road", 359.8, 300),
    ("Regional warehouse 2", "Local warehouse 4", "Road", 526.0, 300),
]
ARCS = [(i, j, mode, km, cap, round(km * RATE[mode], 2)) for i, j, mode, km, cap in NETWORK]

# Forecast 4 (bikes/month) and the share of it that each local warehouse
# receives every month; backorder cost c_b (EUR/(bike*month)), backorders at the
# end of December b_0 and allowed at the end of June b_max (bikes), as in M2
d = dict(zip(T, [240, 440, 400, 800, 840, 500]))
SHARE = {"Local warehouse 1": 0.15, "Local warehouse 2": 0.20, "Local warehouse 3": 0.30, "Local warehouse 4": 0.35}
c_b, b_0, b_max = 60, 0, 0


# ---------------------------------------------------------------------------
# §4 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(nodes, arcs, share, storage):
    """Solve the model on a network: nodes, arcs (origin, destination, mode, km,
    capacity, cost), the share of forecast 4 of each demand node, and the
    storage capacity of each node. Returns (cost, values of each kind of
    variable, shadow prices of the arc, node and storage capacities), or None if
    it has no solution."""
    model = pulp.LpProblem("distribution_network", pulp.LpMinimize)

    def key(node):
        return node.replace(" ", "")

    A = range(len(arcs))
    # p[f, t] = bikes assembled at plant f; x[a, t] = bikes shipped on arc a;
    # h[i, t] = stock of node i at the end of month t; s[i, t] = deliveries and
    # b[i, t] = backorders at the end of month t of demand node i
    p = {(f, t): model.add_variable(f"p_{key(f)}_{t}", lowBound=0) for f in F for t in T}
    x = {(a, t): model.add_variable(f"x_{a}_{t}", lowBound=0) for a in A for t in T}
    h = {(i, t): model.add_variable(f"h_{key(i)}_{t}", lowBound=0) for i in nodes for t in T}
    s = {(i, t): model.add_variable(f"s_{key(i)}_{t}", lowBound=0) for i in share for t in T}
    b = {(i, t): model.add_variable(f"b_{key(i)}_{t}", lowBound=0) for i in share for t in T}

    # Minimise the assembly, holding, transport and backorder cost
    model += (pulp.lpSum(c[f] * p[f, t] for f in F for t in T)
              + pulp.lpSum(c_h[i] * h[i, t] for i in nodes for t in T)
              + pulp.lpSum(arcs[a][5] * x[a, t] for a in A for t in T)
              + pulp.lpSum(c_b * b[i, t] for i in share for t in T))

    for i in nodes:
        into = [a for a in A if arcs[a][1] == i]
        out = [a for a in A if arcs[a][0] == i]
        for k, t in enumerate(T):
            before = h_0[i] if k == 0 else h[i, T[k - 1]]
            assembled = p[i, t] if i in F else 0
            delivered = s[i, t] if i in share else 0
            arriving = pulp.lpSum(x[a, t] for a in into)
            shipped = pulp.lpSum(x[a, t] for a in out)
            # Stock balance at each node
            model += (before + assembled + arriving == shipped + delivered + h[i, t], f"balance_{key(i)}_{t}")
            # Shipment limit at each node: at most the stock of the previous
            # month plus what the node assembles and what arrives
            model += (shipped + delivered <= before + assembled + arriving, f"shipment_limit_{key(i)}_{t}")
            # Storage capacity and node capacity
            model += (h[i, t] <= storage[i], f"storage_{key(i)}_{t}")
            if i in K_n:
                model += (arriving <= K_n[i], f"node_capacity_{key(i)}_{t}")
        # Required final stock
        model += (h[i, T[-1]] >= h_end[i], f"final_stock_{key(i)}")

    for i in share:
        for k, t in enumerate(T):
            before = b_0 if k == 0 else b[i, T[k - 1]]
            # Backorder balance, written with the orders on the right
            model += (s[i, t] + b[i, t] - before == share[i] * d[t], f"backorders_{key(i)}_{t}")
        # No backorders at the end of the horizon
        model += (b[i, T[-1]] <= b_max, f"backorders_at_the_end_{key(i)}")

    # Arc capacity and assembly capacity
    for a in A:
        for t in T:
            model += (x[a, t] <= arcs[a][4], f"arc_capacity_{a}_{t}")
    for f in F:
        for t in T:
            model += (p[f, t] <= K[f][t], f"capacity_{key(f)}_{t}")

    # The solver says whether it found an optimal solution: PuLP 3 returns the
    # status as a number and PuLP 4 as an object with a field status; 1 is
    # optimal in both
    result = model.solve(pulp.HiGHS(msg=False))
    if getattr(result, "status", result) != 1:
        return None

    # The constraints by name, with their shadow prices (pi): a method in
    # PuLP 4, a dict in PuLP 3. They are read here, while the model exists
    constraints = model.constraints() if callable(model.constraints) else model.constraints
    if not isinstance(constraints, dict):
        constraints = {con.name: con for con in constraints}

    def clean(v):                    # no "-0.00" in the tables
        return 0.0 if abs(v) < 1e-9 else v

    values = {kind: {k: clean(var.value()) for k, var in variables.items()}
              for kind, variables in (("p", p), ("x", x), ("h", h), ("s", s), ("b", b))}
    prices = {"arc": {(a, t): clean(constraints[f"arc_capacity_{a}_{t}"].pi) for a in A for t in T},
              "node": {(i, t): clean(constraints[f"node_capacity_{key(i)}_{t}"].pi)
                       for i in K_n if i in nodes for t in T},
              "storage": {(i, t): clean(constraints[f"storage_{key(i)}_{t}"].pi) for i in nodes for t in T}}
    return pulp.value(model.objective), values, prices


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
    print(f"{name:<58}" + "".join(f"{eu(v):>10}" for v in values))


def header():
    print(f"{'':<58}" + "".join(f"{t:>10}" for t in T))


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
    title("§3 Data of the network and forecast 4")
    print("Table 1. Nodes")
    for i in NODES:
        print(f"{i:<24}{PLACES[i]}")
    print()
    print(f"Transport rate (EUR/(bike*km)): road {eu(RATE['Road'], 3)}; rail {eu(RATE['Rail'], 3)}")
    print("Table 2. Arcs")
    print(f"{'Arc':<5}{'Origin -> destination':<52}{'Mode':<6}{'km':>8}{'Cost':>8}{'Capacity':>10}")
    for a, (i, j, mode, km, cap, cost) in enumerate(ARCS):
        print(f"{a + 1:<5}{i + ' -> ' + j:<52}{mode:<6}{eu(km, 1):>8}{eu(cost):>8}{eu(cap, 0):>10}")
    print()
    print("Table 3. Nodes: holding cost, storage capacity, initial stock,")
    print("required final stock, node capacity")
    for i in NODES:
        print(f"{i:<24}{c_h[i]:>5}{K_h[i]:>6}{h_0[i]:>6}{h_end[i]:>6}{K_n.get(i, '-'):>6}")
    print()
    print("Table 4. Forecast 4 and the orders of each local warehouse (bikes/month)")
    header()
    for i in LOCAL:
        by_month(f"{i} ({eu(100 * SHARE[i], 0)} %)", [SHARE[i] * d[t] for t in T])
    by_month("Forecast 4", [d[t] for t in T])

    # §1 M2 with forecast 4: the plants and the central warehouse, which receives
    # all the orders, without the regional and local warehouses
    m2_arcs = [arc for arc in ARCS if arc[1] == CENTRAL]
    m2 = solve_model(F + [CENTRAL], m2_arcs, {CENTRAL: 1.0}, K_h)
    print()
    print(f"M2 (plants and central warehouse only) has a solution with forecast 4: {'yes' if m2 else 'no'}")

    # §6 Plan of M3 with forecast 4
    title("§6.1 Optimal plan under forecast 4")
    cost, v, prices = solve_model(NODES, ARCS, SHARE, K_h)
    print("Table 6. Bikes assembled")
    header()
    for f in F:
        by_month(f, [v["p"][f, t] for t in T])
    print()
    print("Table 7. Flow on each arc (bikes)")
    header()
    for a, arc in enumerate(ARCS):
        by_month(f"{a + 1}. {arc[0]} -> {arc[1]}", [v["x"][a, t] for t in T])
    print()
    print("Table 8. Stock at the end of the month (bikes)")
    header()
    for i in NODES:
        by_month(i, [v["h"][i, t] for t in T])
    print()
    same = all(abs(v["s"][i, t] - SHARE[i] * d[t]) < 1e-6 for i in LOCAL for t in T)
    print(f"Deliveries of each local warehouse equal its orders (Table 4) every month: {'yes' if same else 'no'}")
    print(f"Backorders, all local warehouses and months: {eu(sum(v['b'].values()))}")
    print(f"Cost: {eu(cost)} EUR")

    title("§6.3 Shadow prices of the full capacities")
    print("Table 9. Shadow prices (EUR/bike)")
    header()
    for a, arc in enumerate(ARCS):
        if any(prices["arc"][a, t] for t in T):
            by_month(f"Arc capacity, {a + 1}. {arc[0]} -> {arc[1]}", [prices["arc"][a, t] for t in T])
    for i in K_n:
        by_month(f"Node capacity, {i}", [prices["node"][i, t] for t in T])
    for i in NODES:
        if i != TERMINAL and any(prices["storage"][i, t] for t in T):
            by_month(f"Storage capacity, {i}", [prices["storage"][i, t] for t in T])
