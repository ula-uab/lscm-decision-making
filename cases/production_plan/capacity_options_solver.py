# Production plan with capacity options (M4B)
#
# This script reproduces every table of capacity_options.md (same folder)
# except Table 3, the notation: the base forecast with the orders of each
# retailer and the price of each month (Table 1), the capacity options
# (Table 2), the plan under the base forecast (Tables 4 and 5), the plans
# under a demand growth (Table 6), the plans under a price promotion
# (Table 7) and the plans with plant 3 closed (Table 8), with the plans in
# which the model decides whether plant 3 is open.
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
#     Windows:          python capacity_options_solver.py
#     macOS and Linux:  python3 capacity_options_solver.py

import sys

import pulp


# ---------------------------------------------------------------------------
# Data of M4 (retailers.md), unchanged, and §2 Data of M4B (Tables 1 and 2).
# Invented (2026), except the places and distances
# ---------------------------------------------------------------------------

T = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]        # months
F = ["Plant 1", "Plant 2", "Plant 3"]                 # assembly plants
CENTRAL, TERMINAL = "Central warehouse", "Rail terminal"
REGIONAL = ["Regional warehouse 1", "Regional warehouse 2"]
LOCAL = ["Local warehouse 1", "Local warehouse 2", "Local warehouse 3", "Local warehouse 4"]
NODES = F + [CENTRAL, TERMINAL] + REGIONAL + LOCAL
RETAILERS = ["Retailer 1", "Retailer 2", "Retailer 3", "Retailer 4", "Retailer 5", "Retailer 6"]

# Place of each node and of each retailer (Nominatim, OpenStreetMap,
# consulted on 23/10/2026)
PLACES = {"Plant 1": "Vitoria-Gasteiz", "Plant 2": "Pamplona", "Plant 3": "Castellón de la Plana",
          CENTRAL: "Zaragoza", TERMINAL: "Coslada", "Regional warehouse 1": "Barcelona",
          "Regional warehouse 2": "Getafe", "Local warehouse 1": "Girona", "Local warehouse 2": "Tarragona",
          "Local warehouse 3": "Valencia", "Local warehouse 4": "Seville",
          "Retailer 1": "Lleida", "Retailer 2": "Sabadell", "Retailer 3": "Alicante",
          "Retailer 4": "Murcia", "Retailer 5": "Córdoba", "Retailer 6": "Granada"}

# Unit assembly cost c[f] (EUR/bike) and assembly capacity K[f][t] (bikes/month)
c = {"Plant 1": 310, "Plant 2": 340, "Plant 3": 390}
K = {f: {t: cap for t in T} for f, cap in {"Plant 1": 250, "Plant 2": 200, "Plant 3": 150}.items()}

# Holding cost c_h[i] (EUR/(bike*month)), storage capacity K_h[i] (bikes), initial
# stock h_0[i] and required final stock h_end[i] (bikes) of every node; the
# retailers hold no stock
c_h = {"Plant 1": 5, "Plant 2": 6, "Plant 3": 7, CENTRAL: 8, TERMINAL: 0,
       "Regional warehouse 1": 9, "Regional warehouse 2": 10,
       "Local warehouse 1": 11, "Local warehouse 2": 12, "Local warehouse 3": 13, "Local warehouse 4": 14}
K_h = {"Plant 1": 40, "Plant 2": 30, "Plant 3": 20, CENTRAL: 150, TERMINAL: 0,
       "Regional warehouse 1": 60, "Regional warehouse 2": 60,
       "Local warehouse 1": 20, "Local warehouse 2": 20, "Local warehouse 3": 20, "Local warehouse 4": 20}
c_h.update({r: 0 for r in RETAILERS})
K_h.update({r: 0 for r in RETAILERS})
h_0 = {i: {"Plant 1": 20, "Plant 2": 10}.get(i, 0) for i in NODES + RETAILERS}
h_end = dict(h_0)

# Node capacity K_n[i]: bikes the node can receive in a month
K_n = {"Regional warehouse 2": 280}

# Transport rate of each mode (EUR/(bike*km)), invented
RATE = {"Road": 0.010, "Rail": 0.006}

# The network as a list of arcs: origin, destination, mode, distance (km) and arc
# capacity (bikes/month). Distances: OSRM (road) and OpenRailRouting (rail), on
# OpenStreetMap data, consulted on 23/10/2026. The transport cost of an arc is its
# distance times the rate of its mode, rounded to the cent (EUR/bike)
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
ARCS = [(i, j, mode, km, cap, round(km * RATE[mode], 2)) for i, j, mode, km, cap in NETWORK]

# Share of the orders of each retailer, its backorder share beta[r] (the rest is
# lost sales), backorder cost c_b (EUR/(bike*month)) and backorders at the end of
# December b_0 (bikes)
SHARE = dict(zip(RETAILERS, [0.14, 0.22, 0.18, 0.16, 0.20, 0.10]))
BETA = dict(zip(RETAILERS, [0.9, 0.7, 0.5, 0.8, 0.6, 0.4]))
c_b, b_0 = 60, 0

# New in M4B: the base forecast D[t] (bikes/month), the price of each month
# (EUR/bike), the maximum overtime of each plant (bikes/month) with its extra
# cost (EUR/bike), the rented storage next to the central warehouse (bikes) with
# its cost (EUR/(bike*month)), and the fixed cost of each open plant (EUR/month)
D = dict(zip(T, [200, 400, 350, 700, 700, 450]))
PRICE = {t: 700 for t in T}
o_max = {"Plant 1": 25, "Plant 2": 20, "Plant 3": 0}
c_o = 100
u_max = 200
c_u = 12
c_F = {"Plant 1": 0, "Plant 2": 0, "Plant 3": 20000}

STAGES = [("Plants", F), ("Central warehouse", [CENTRAL]), ("Regional warehouses", REGIONAL),
          ("Local warehouses", LOCAL)]
PLANT_3 = "Plant 3"


# ---------------------------------------------------------------------------
# §3 The model, written with PuLP and solved with HiGHS
# ---------------------------------------------------------------------------

def orders(growth=0.0):
    """The orders of each retailer in each month (bikes): its share of the base
    forecast of the month raised by the demand growth of that month. The growth is
    one number for every month or a growth by month."""
    rise = growth if isinstance(growth, dict) else {t: growth for t in T}
    return {(r, t): SHARE[r] * D[t] * (1 + rise[t]) for r in RETAILERS for t in T}


def solve_model(growth=0.0, price=None, plant_3="open", overtime=False, rented=0.0, fixed_cost=0.0):
    """Solve M4B. ``growth`` is the demand growth, one number for every month or a
    growth by month, and ``price`` the price of each month (EUR/bike), 700 in every
    month by default. ``plant_3`` is "open", "closed" or "model", which leaves the
    decision to the model; ``overtime`` says whether plants 1 and 2 can work
    overtime, ``rented`` how many bikes can be rented next to the central warehouse,
    and ``fixed_cost`` the fixed cost of plant 3 (EUR/month). Returns the cost and
    the margin of the plan (EUR), the values of each kind of variable, whether
    plant 3 is open, and the orders of each retailer; or None if it has no
    solution."""
    price = price or PRICE
    order = orders(growth)
    o_top = o_max if overtime else {f: 0 for f in F}
    model = pulp.LpProblem("capacity_options", pulp.LpMinimize)

    def key(node):
        return node.replace(" ", "")

    nodes = NODES + RETAILERS
    A = range(len(ARCS))
    # p[f, t] = bikes assembled, o[f, t] = of them, assembled in overtime;
    # x[a, t] = bikes shipped on arc a; h[i, t] = stock at the end of month t,
    # u[t] = of it, in rented storage; s, b, l = deliveries, backorders at the end
    # of month t and lost sales of each retailer
    p = {(f, t): model.add_variable(f"p_{key(f)}_{t}", lowBound=0) for f in F for t in T}
    o = {(f, t): model.add_variable(f"o_{key(f)}_{t}", lowBound=0) for f in F for t in T}
    x = {(a, t): model.add_variable(f"x_{a}_{t}", lowBound=0) for a in A for t in T}
    h = {(i, t): model.add_variable(f"h_{key(i)}_{t}", lowBound=0) for i in nodes for t in T}
    u = {t: model.add_variable(f"u_{t}", lowBound=0) for t in T}
    s = {(r, t): model.add_variable(f"s_{key(r)}_{t}", lowBound=0) for r in RETAILERS for t in T}
    b = {(r, t): model.add_variable(f"b_{key(r)}_{t}", lowBound=0) for r in RETAILERS for t in T}
    l = {(r, t): model.add_variable(f"l_{key(r)}_{t}", lowBound=0) for r in RETAILERS for t in T}
    # delta[f] = 1 if plant f is open from January to June: plants 1 and 2 always
    # are; plant 3 is open, closed, or a binary variable of the model
    delta = {f: 1 for f in F}
    if plant_3 == "closed":
        delta[PLANT_3] = 0
    elif plant_3 == "model":
        delta[PLANT_3] = model.add_variable(f"delta_{key(PLANT_3)}", cat="Binary")

    # Minimise the assembly, overtime, holding, rented storage, transport,
    # backorder and lost-sale cost, plus the fixed cost of the plants that are open
    fixed = {**c_F, PLANT_3: fixed_cost}
    model += (pulp.lpSum(c[f] * p[f, t] + c_o * o[f, t] for f in F for t in T)
              + pulp.lpSum(c_h[i] * h[i, t] for i in nodes for t in T)
              + pulp.lpSum(c_u * u[t] for t in T)
              + pulp.lpSum(ARCS[a][5] * x[a, t] for a in A for t in T)
              + pulp.lpSum(c_b * b[r, t] + price[t] * l[r, t] for r in RETAILERS for t in T)
              + pulp.lpSum(len(T) * fixed[f] * delta[f] for f in F))

    for i in nodes:
        into = [a for a in A if ARCS[a][1] == i]
        out = [a for a in A if ARCS[a][0] == i]
        for k, t in enumerate(T):
            before = h_0[i] if k == 0 else h[i, T[k - 1]]
            assembled = p[i, t] if i in F else 0
            delivered = s[i, t] if i in RETAILERS else 0
            arriving = pulp.lpSum(x[a, t] for a in into)
            shipped = pulp.lpSum(x[a, t] for a in out)
            # Stock balance at each node
            model += (before + assembled + arriving == shipped + delivered + h[i, t], f"balance_{key(i)}_{t}")
            # Shipment limit at each node: at most the stock of the previous month
            # plus what the node assembles and what arrives
            model += (shipped + delivered <= before + assembled + arriving, f"shipment_limit_{key(i)}_{t}")
            # Storage capacity, relaxed at the central warehouse by the rented storage
            rent = u[t] if i == CENTRAL else 0
            model += (h[i, t] - rent <= K_h[i], f"storage_{key(i)}_{t}")
            if i in K_n:
                model += (arriving <= K_n[i], f"node_capacity_{key(i)}_{t}")
        # Required final stock
        model += (h[i, T[-1]] >= h_end[i], f"final_stock_{key(i)}")

    # Rented storage
    for t in T:
        model += (u[t] <= rented, f"rented_storage_{t}")

    for r in RETAILERS:
        for k, t in enumerate(T):
            before = b_0 if k == 0 else b[r, T[k - 1]]
            # Backorder balance, written with the orders on the right
            model += (s[r, t] + b[r, t] + l[r, t] - before == order[r, t], f"backorders_{key(r)}_{t}")
            # Backorder share, from January to May
            if k < len(T) - 1:
                model += (b[r, t] == BETA[r] * (before + order[r, t] - s[r, t]), f"backorder_share_{key(r)}_{t}")
        # No backorders at the end of June
        model += (b[r, T[-1]] == 0, f"backorders_at_the_end_{key(r)}")

    # Arc capacity, assembly capacity relaxed by the overtime, and overtime
    for a in A:
        for t in T:
            model += (x[a, t] <= ARCS[a][4], f"arc_capacity_{a}_{t}")
    for f in F:
        for t in T:
            model += (p[f, t] - o[f, t] <= K[f][t] * delta[f], f"capacity_{key(f)}_{t}")
            model += (o[f, t] <= o_top[f] * delta[f], f"overtime_{key(f)}_{t}")

    # The solver says whether it found an optimal solution: PuLP 3 returns the
    # status as a number and PuLP 4 as an object with a field status; 1 is
    # optimal in both
    result = model.solve(pulp.HiGHS(msg=False))
    if getattr(result, "status", result) != 1:
        return None

    def clean(v):                    # no "-0,00" in the tables
        return 0.0 if abs(v) < 1e-6 else v

    values = {kind: {k: clean(var.value()) for k, var in variables.items()}
              for kind, variables in (("p", p), ("o", o), ("x", x), ("h", h), ("s", s), ("b", b), ("l", l))}
    values["u"] = {t: clean(u[t].value()) for t in T}
    cost = pulp.value(model.objective)
    # The lost-sale cost of a month is its price, so the price of the orders less
    # the cost of the plan is the margin of the plan
    margin = sum(price[t] * order[r, t] for r in RETAILERS for t in T) - cost
    open_3 = 1 if plant_3 == "open" else (0 if plant_3 == "closed" else round(delta[PLANT_3].value()))
    return {"cost": cost, "margin": margin, "values": values, "orders": order, "plant 3 open": open_3}


def total(solution, kind, key=None):
    """What a kind of variable adds up to in the horizon, for one key or for all."""
    values = solution["values"][kind]
    return sum(v for k, v in values.items() if key is None or (k[0] if isinstance(k, tuple) else k) == key)


def utilization(solution, plant):
    """The capacity utilization of a plant: what it assembles in the horizon, as a
    share of the sum of its capacities."""
    return total(solution, "p", plant) / sum(K[plant][t] for t in T)


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


def header(width=48):
    print(f"{'':<{width}}" + "".join(f"{t:>10}" for t in T))


def by_month(name, values, decimals=2, width=48):
    print(f"{name:<{width}}" + "".join(f"{eu(v, decimals):>10}" for v in values))


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

    # §2 Data
    title("§2 Base forecast, orders of each retailer and price")
    print("Table 1. Base forecast, orders of each retailer (bikes/month) and price (EUR/bike)")
    header()
    order = orders()
    for r in RETAILERS:
        by_month(f"{r} ({PLACES[r]}), share {eu(100 * SHARE[r], 0)} %", [order[r, t] for t in T], 0)
    by_month("Base forecast", [D[t] for t in T], 0)
    by_month("Price", [PRICE[t] for t in T], 0)
    print(f"Orders in the six months: {eu(sum(order.values()), 0)} bikes; "
          f"capacity of the three plants: {eu(sum(K[f][t] for f in F for t in T), 0)} bikes")
    print()
    print("Table 2. Capacity options")
    for f in F:
        print(f"{'Overtime at ' + f.lower():<48}{eu(o_max[f], 0):>10} bikes/month")
    print(f"{'Extra cost of a bike assembled in overtime':<48}{eu(c_o, 0):>10} EUR/bike")
    print(f"{'Rented storage next to the central warehouse':<48}{eu(u_max, 0):>10} bikes")
    print(f"{'Cost of the rented storage':<48}{eu(c_u, 0):>10} EUR/(bike*month)")
    print(f"{'Fixed cost of plant 3 open':<48}{eu(c_F[PLANT_3], 0):>10} EUR/month")

    # §5.1 Plan under the base forecast
    title("§5.1 Optimal plan under the base forecast")
    base = solve_model()
    print(f"Cost: {eu(base['cost'])} EUR; margin: {eu(base['margin'])} EUR; "
          f"lost sales: {eu(total(base, 'l'), 0)} bikes")
    print()
    print("Table 4. Bikes assembled (bikes/month)")
    header()
    for f in F:
        by_month(f, [base["values"]["p"][f, t] for t in T], 0)
    print("Capacity utilization: " + "; ".join(f"{f} {eu(100 * utilization(base, f), 1)} %" for f in F))
    print()
    print("Table 5. Seasonal stock at the end of each month, by stage (bikes)")
    header()
    for name, group in STAGES:
        by_month(name, [sum(base["values"]["h"][i, t] for i in group) for t in T], 0)
    by_month("Total", [sum(base["values"]["h"][i, t] for _, group in STAGES for i in group) for t in T], 0)

    # §5.2 Plans under a demand growth
    title("§5.2 Plans under a demand growth")
    print("Table 6. Plans under a demand growth")
    print(f"{'Growth':>8}{'Orders':>12}{'Cost (EUR)':>18}{'Margin (EUR)':>18}"
          f"{'Plant 3':>10}{'Lost sales':>12}")
    for growth in [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
        plan = solve_model(growth=growth)
        print(f"{eu(100 * growth, 0) + ' %':>8}{eu(sum(plan['orders'].values()), 0):>12}"
              f"{eu(plan['cost']):>18}{eu(plan['margin']):>18}"
              f"{eu(100 * utilization(plan, PLANT_3), 1) + ' %':>10}{eu(total(plan, 'l'), 1):>12}")
    rent = solve_model(growth=0.25, rented=u_max)
    print(f"With a growth of 25 % and rented storage: cost {eu(rent['cost'])} EUR; "
          f"margin {eu(rent['margin'])} EUR; lost sales {eu(total(rent, 'l'), 0)}; "
          f"plant 3 {eu(100 * utilization(rent, PLANT_3), 1)} %; "
          f"rented in March {eu(rent['values']['u']['Mar'], 0)} bikes")

    # §5.3 Plans under a price promotion
    title("§5.3 Plans under a price promotion")
    print("Table 7. Plans under a price promotion")
    print(f"{'Months':>20}{'Discount':>10}{'Growth':>10}{'Rented':>10}{'Margin (EUR)':>18}"
          f"{'Plant 3':>10}{'Lost sales':>12}")
    for months, discount, growth, rented in [(["Jan", "Feb", "Mar"], 0.15, 0.51, 0),
                                             (["Apr", "May"], 0.05, 0.14, 0),
                                             (["Apr", "May"], 0.075, 0.17, 0),
                                             (["Apr", "May"], 0.075, 0.24, 0),
                                             (["Apr", "May"], 0.10, 0.33, u_max)]:
        price = {t: PRICE[t] * (1 - discount) if t in months else PRICE[t] for t in T}
        rise = {t: growth if t in months else 0.0 for t in T}
        plan = solve_model(growth=rise, price=price, rented=rented)
        print(f"{', '.join(months):>20}{eu(100 * discount, 1) + ' %':>10}"
              f"{eu(100 * growth, 0) + ' %':>10}{('yes' if rented else 'no'):>10}"
              f"{eu(plan['margin']):>18}{eu(100 * utilization(plan, PLANT_3), 1) + ' %':>10}"
              f"{eu(total(plan, 'l'), 1):>12}")
    print(f"Margin of the plan without promotion: {eu(base['margin'])} EUR")

    # §5.4 Plans with plant 3 closed
    title("§5.4 Plans with plant 3 closed")
    print("Table 8. Plans with plant 3 closed, under the base forecast")
    print(f"{'Capacity options':>30}{'Cost (EUR)':>18}{'Margin (EUR)':>18}"
          f"{'Lost sales':>12}{'Overtime':>10}{'Rented':>10}")
    for name, overtime, rented in [("None", False, 0), ("Overtime", True, 0),
                                   ("Rented storage", False, u_max),
                                   ("Overtime and rented storage", True, u_max)]:
        plan = solve_model(plant_3="closed", overtime=overtime, rented=rented)
        print(f"{name:>30}{eu(plan['cost']):>18}{eu(plan['margin']):>18}"
              f"{eu(total(plan, 'l'), 0):>12}{eu(total(plan, 'o'), 0):>10}"
              f"{eu(max(plan['values']['u'].values()), 0):>10}")
    print()
    print("Plant 3 left to the model, with its fixed cost and both capacity options:")
    for growth in [0, 0.10, 0.15, 0.18, 0.20]:
        plan = solve_model(growth=growth, plant_3="model", overtime=True, rented=u_max,
                           fixed_cost=c_F[PLANT_3])
        print(f"   growth {eu(100 * growth, 0):>5} %: plant 3 "
              f"{'open' if plan['plant 3 open'] else 'closed'}; cost {eu(plan['cost'])} EUR "
              f"(the fixed cost included)")
