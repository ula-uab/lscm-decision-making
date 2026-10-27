# Production plan with retailers (M4)
#
# This script reproduces every table of retailers.md (same folder): the
# retailers, their arcs, their orders, backorder shares and lost-sale cost
# (Tables 1 to 3); that M3, with the orders at the local warehouses, has no
# solution with forecast 5; the plan of M4 with forecast 5 (Tables 5 to 8); and
# the shadow prices of the capacities that are full (Table 9).
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
#     Windows:          python retailers_solver.py
#     macOS and Linux:  python3 retailers_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# Data of M3 (distribution_network.md), unchanged, and §3 Data of M4 (Tables 1
# to 3). Invented (2026), except the places and distances
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

# Share of the demand that each local warehouse received in M3; backorder cost
# c_b (EUR/(bike*month)) and backorders at the end of December b_0 (bikes), as in M2
SHARE_M3 = {"Local warehouse 1": 0.15, "Local warehouse 2": 0.20, "Local warehouse 3": 0.30, "Local warehouse 4": 0.35}
c_b, b_0, b_max = 60, 0, 0

# New in M4: the retailers (Nominatim, OpenStreetMap, consulted on 23/10/2026),
# which hold no stock
RETAILERS = ["Retailer 1", "Retailer 2", "Retailer 3", "Retailer 4", "Retailer 5", "Retailer 6"]
PLACES.update({"Retailer 1": "Lleida", "Retailer 2": "Sabadell", "Retailer 3": "Alicante",
               "Retailer 4": "Murcia", "Retailer 5": "Córdoba", "Retailer 6": "Granada"})
for r in RETAILERS:
    c_h[r], K_h[r], h_0[r], h_end[r] = 0, 0, 0, 0

# The arcs from the local warehouses to the retailers (OSRM, consulted on
# 23/10/2026): origin, destination, mode, distance (km), arc capacity (bikes/month)
NETWORK_M4 = NETWORK + [
    ("Local warehouse 2", "Retailer 1", "Road", 97.0, 1000),
    ("Local warehouse 1", "Retailer 1", "Road", 225.9, 1000),
    ("Local warehouse 1", "Retailer 2", "Road", 92.3, 1000),
    ("Local warehouse 2", "Retailer 2", "Road", 104.7, 1000),
    ("Local warehouse 3", "Retailer 3", "Road", 177.1, 1000),
    ("Local warehouse 4", "Retailer 3", "Road", 600.3, 1000),
    ("Local warehouse 3", "Retailer 4", "Road", 223.7, 1000),
    ("Local warehouse 4", "Retailer 4", "Road", 531.2, 1000),
    ("Local warehouse 4", "Retailer 5", "Road", 144.1, 150),
    ("Local warehouse 3", "Retailer 5", "Road", 521.3, 1000),
    ("Local warehouse 4", "Retailer 6", "Road", 254.3, 1000),
    ("Local warehouse 3", "Retailer 6", "Road", 478.4, 1000),
]
ARCS_M4 = [(i, j, mode, km, cap, round(km * RATE[mode], 2)) for i, j, mode, km, cap in NETWORK_M4]

# Forecast 5 (bikes/month), the share of it that each retailer receives every
# month, the backorder share beta[r] of each retailer (the rest is lost sales) and
# the lost-sale cost c_l (EUR/bike), the price that a retailer pays for a bike
d = dict(zip(T, [250, 500, 450, 900, 900, 550]))
SHARE = dict(zip(RETAILERS, [0.14, 0.22, 0.18, 0.16, 0.20, 0.10]))
BETA = dict(zip(RETAILERS, [0.9, 0.7, 0.5, 0.8, 0.6, 0.4]))
c_l = 700


# ---------------------------------------------------------------------------
# §4 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def solve_model(nodes, arcs, share, retailers=True):
    """Solve the model on a network: nodes, arcs (origin, destination, mode, km,
    capacity, cost) and the share of forecast 5 of each demand node. With
    retailers=True (M4), the demand nodes are retailers: of the demand not
    delivered in its month, the backorder share is backordered and the rest is
    lost sales, and no order is pending at the end of June. With retailers=False
    (M3), every order has to be delivered by the end of June. Returns (cost,
    values of each kind of variable, shadow prices of the arc, node and storage
    capacities), or None if it has no solution."""
    model = pulp.LpProblem("retailers", pulp.LpMinimize)

    def key(node):
        return node.replace(" ", "")

    A = range(len(arcs))
    # p[f, t] = bikes assembled; x[a, t] = bikes shipped on arc a; h[i, t] = stock
    # at the end of month t; s[i, t] = deliveries, b[i, t] = backorders at the end
    # of month t and l[i, t] = lost sales of demand node i
    p = {(f, t): model.add_variable(f"p_{key(f)}_{t}", lowBound=0) for f in F for t in T}
    x = {(a, t): model.add_variable(f"x_{a}_{t}", lowBound=0) for a in A for t in T}
    h = {(i, t): model.add_variable(f"h_{key(i)}_{t}", lowBound=0) for i in nodes for t in T}
    s = {(i, t): model.add_variable(f"s_{key(i)}_{t}", lowBound=0) for i in share for t in T}
    b = {(i, t): model.add_variable(f"b_{key(i)}_{t}", lowBound=0) for i in share for t in T}
    l = {(i, t): model.add_variable(f"l_{key(i)}_{t}", lowBound=0, upBound=None if retailers else 0)
         for i in share for t in T}

    # Minimise the assembly, holding, transport, backorder and lost-sale cost
    model += (pulp.lpSum(c[f] * p[f, t] for f in F for t in T)
              + pulp.lpSum(c_h[i] * h[i, t] for i in nodes for t in T)
              + pulp.lpSum(arcs[a][5] * x[a, t] for a in A for t in T)
              + pulp.lpSum(c_b * b[i, t] + c_l * l[i, t] for i in share for t in T))

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
            model += (h[i, t] <= K_h[i], f"storage_{key(i)}_{t}")
            if i in K_n:
                model += (arriving <= K_n[i], f"node_capacity_{key(i)}_{t}")
        # Required final stock
        model += (h[i, T[-1]] >= h_end[i], f"final_stock_{key(i)}")

    for i in share:
        for k, t in enumerate(T):
            before = b_0 if k == 0 else b[i, T[k - 1]]
            # Backorder balance, written with the orders on the right
            model += (s[i, t] + b[i, t] + l[i, t] - before == share[i] * d[t], f"backorders_{key(i)}_{t}")
            # Backorder share, from January to May (M4 only)
            if retailers and k < len(T) - 1:
                model += (b[i, t] == BETA[i] * (before + share[i] * d[t] - s[i, t]), f"backorder_share_{key(i)}_{t}")
        # No backorders at the end of June
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
              for kind, variables in (("p", p), ("x", x), ("h", h), ("s", s), ("b", b), ("l", l))}
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
    title("§3 Retailer data and forecast 5")
    print("Table 1. Retailers")
    for r in RETAILERS:
        print(f"{r:<14}{PLACES[r]}")
    print()
    print("Table 2. Arcs from the local warehouses to the retailers")
    print(f"{'Arc':<5}{'Origin -> destination':<40}{'km':>8}{'Cost':>8}{'Capacity':>10}")
    for a, (i, j, mode, km, cap, cost) in enumerate(ARCS_M4):
        if j in RETAILERS:
            print(f"{a + 1:<5}{i + ' -> ' + j:<40}{eu(km, 1):>8}{eu(cost):>8}{eu(cap, 0):>10}")
    print()
    print("Table 3. Orders of each retailer (bikes/month), backorder share and lost-sale cost")
    header()
    for r in RETAILERS:
        by_month(f"{r} ({eu(100 * SHARE[r], 0)} %; backorder share {eu(BETA[r], 1)})", [SHARE[r] * d[t] for t in T])
    by_month("Forecast 5", [d[t] for t in T])
    print(f"Lost-sale cost: {eu(c_l)} EUR/bike; backorder cost: {eu(c_b)} EUR/(bike*month)")

    # §1 M3 with forecast 5: the network of M3, with the orders at the local
    # warehouses split as in M3 and no lost sales
    m3 = solve_model(NODES, ARCS, SHARE_M3, retailers=False)
    print()
    print(f"M3 (orders at the local warehouses) has a solution with forecast 5: {'yes' if m3 else 'no'}")

    # §6 Plan of M4 with forecast 5
    title("§6.1 Optimal plan under forecast 5")
    cost, v, prices = solve_model(NODES + RETAILERS, ARCS_M4, SHARE)
    print("Table 5. Bikes assembled")
    header()
    for f in F:
        by_month(f, [v["p"][f, t] for t in T])
    print()
    print("Table 6. Flow on each arc (bikes)")
    header()
    for a, arc in enumerate(ARCS_M4):
        by_month(f"{a + 1}. {arc[0]} -> {arc[1]}", [v["x"][a, t] for t in T])
    print()
    print("Table 7. Stock at the end of the month (bikes)")
    header()
    for i in NODES:
        by_month(i, [v["h"][i, t] for t in T])
    print()
    print("Table 8. Deliveries, backorders and lost sales of the retailers (bikes)")
    header()
    for label, kind in (("Deliveries", "s"), ("Backorders", "b"), ("Lost sales", "l")):
        for r in RETAILERS:
            by_month(f"{label}, {r} ({PLACES[r]})", [v[kind][r, t] for t in T])
    print(f"Lost sales, all retailers: {eu(sum(v['l'].values()))} of {eu(sum(d.values()))} orders")
    print(f"Cost: {eu(cost)} EUR")

    title("§6.3 Shadow prices of the full capacities")
    print("Table 9. Shadow prices (EUR/bike)")
    header()
    for a, arc in enumerate(ARCS_M4):
        if any(prices["arc"][a, t] for t in T):
            by_month(f"Arc capacity, {a + 1}. {arc[0]} -> {arc[1]}", [prices["arc"][a, t] for t in T])
    for i in NODES:
        if i != TERMINAL and any(prices["storage"][i, t] for t in T):
            by_month(f"Storage capacity, {i}", [prices["storage"][i, t] for t in T])
