# Expanded network: generalized assignment, set covering and set partitioning
#
# This script reproduces every table of expanded_network.md (same folder) except
# the notation (Table 4): the retailers, the local warehouses and the distances
# (Tables 1 to 3); the four plans of the assignment of retailers to local
# warehouses (Tables 5 to 7); the regional warehouses (Tables 8 and 9); and the
# weekly routes of local warehouse 2 (Tables 10 to 13). It also checks that each
# optimal plan is the only one.
#
# The models are written with the PuLP library and solved by the HiGHS solver to
# their exact optimum.
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later and two free libraries:
#   - PuLP: writes the optimisation models;
#   - highspy: the HiGHS solver, which solves the models written with PuLP.
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
#     Windows:          python expanded_network_solver.py
#     macOS and Linux:  python3 expanded_network_solver.py

import itertools

import pulp


# ---------------------------------------------------------------------------
# §2 Data (Tables 1 to 3, 8, 10 and 11). Invented (2026), except the places, the
# populations, the distances and the travel times
# ---------------------------------------------------------------------------

# Retailers 1 to 46: place and population of the city (municipal register at 1
# January 2025, INE). Retailers 1 to 6 are those of M4
RETAILERS = [
    ("Lleida", 146266),
    ("Sabadell", 225368),
    ("Alicante", 366221),
    ("Murcia", 479405),
    ("Córdoba", 323262),
    ("Granada", 233975),
    ("Barcelona", 1731649),
    ("Girona", 108666),
    ("Tarragona", 143649),
    ("Manresa", 80974),
    ("Zaragoza", 693091),
    ("Huesca", 55454),
    ("Castellón de la Plana", 183711),
    ("Valencia", 840792),
    ("Gandía", 83135),
    ("Elche", 245557),
    ("Cartagena", 220704),
    ("Albacete", 175400),
    ("Almería", 205468),
    ("Jaén", 112235),
    ("Seville", 689423),
    ("Málaga", 599063),
    ("Marbella", 159786),
    ("Huelva", 143215),
    ("Cádiz", 109950),
    ("Madrid", 3506730),
    ("Alcobendas", 123342),
    ("Toledo", 87216),
    ("Guadalajara", 92834),
    ("Segovia", 52375),
    ("Ciudad Real", 76217),
    ("Cuenca", 53600),
    ("Valladolid", 302614),
    ("Burgos", 177402),
    ("León", 123446),
    ("Salamanca", 146110),
    ("Bilbao", 351124),
    ("San Sebastián", 189866),
    ("Santander", 175425),
    ("Logroño", 152150),
    ("Oviedo", 223968),
    ("Gijón", 269894),
    ("A Coruña", 251543),
    ("Vigo", 294489),
    ("Badajoz", 150209),
    ("Cáceres", 96651),
]
# Local warehouses 1 to 12 and their node capacity (bikes/year), invented.
# Local warehouses 1 to 4 are those of M3
LOCAL = [
    ("Girona", 1000),
    ("Tarragona", 6000),
    ("Valencia", 3000),
    ("Seville", 4500),
    ("Murcia", 5500),
    ("Málaga", 3000),
    ("Alcalá de Henares", 5500),
    ("Valladolid", 2500),
    ("Bilbao", 3000),
    ("Oviedo", 2000),
    ("Santiago de Compostela", 2000),
    ("Badajoz", 1500),
]
# Road distance (km) from each local warehouse (row) to retailers 1 to 46 (OSRM,
# 10/11/2026; the twelve arcs of M4 keep the distances of retailers.md)
ROAD_KM = [
    [225.9, 92.3, 627.8, 674.5, 954.1, 929.3, 102.7, 0.0, 189.0, 118.1, 380.7, 342.7, 372.0, 442.6, 520.5, 624.7, 715.3, 603.2, 858.5, 892.5, 1091.5, 1054.8, 1099.8, 1180.3, 1200.8, 687.5, 682.5, 760.3, 630.7, 785.0, 785.6, 631.8, 800.3, 672.5, 841.6, 912.1, 676.9, 637.5, 774.1, 544.2, 963.6, 940.1, 1148.2, 1214.9, 1087.4, 985.5],
    [97.0, 104.7, 444.8, 491.5, 771.1, 746.3, 96.4, 188.1, 0.0, 113.2, 234.7, 213.3, 189.1, 259.6, 337.5, 441.7, 532.3, 420.2, 675.5, 709.5, 908.5, 871.8, 916.8, 997.3, 1017.8, 541.6, 536.5, 614.4, 484.8, 639.1, 602.6, 448.8, 654.4, 526.6, 695.7, 766.1, 531.0, 492.1, 628.2, 398.2, 817.7, 794.2, 1002.3, 1069.0, 941.5, 839.5],
    [348.0, 358.9, 177.1, 223.7, 521.3, 478.4, 350.6, 442.3, 259.3, 367.4, 321.8, 388.1, 76.7, 0.0, 69.7, 173.8, 264.4, 186.4, 407.6, 459.8, 658.7, 604.0, 649.0, 747.5, 768.0, 356.1, 369.0, 373.7, 384.8, 452.9, 352.9, 199.1, 542.9, 587.4, 694.1, 572.9, 612.4, 573.5, 709.6, 479.6, 806.3, 824.6, 947.1, 952.9, 660.4, 629.2],
    [989.0, 1007.6, 600.3, 531.2, 144.1, 254.3, 999.2, 1091.0, 907.9, 1016.0, 844.7, 912.6, 725.3, 657.4, 661.5, 577.5, 531.2, 487.5, 410.8, 253.7, 0.0, 212.9, 266.2, 90.9, 123.2, 531.8, 550.0, 493.3, 587.9, 605.8, 328.3, 567.6, 581.1, 704.9, 664.5, 459.1, 858.7, 913.9, 824.1, 834.0, 776.7, 795.1, 917.6, 737.4, 207.2, 261.7],
    [579.7, 590.6, 89.1, 0.0, 439.4, 281.4, 582.2, 674.0, 491.0, 599.1, 529.3, 595.6, 308.3, 223.2, 197.5, 66.6, 48.9, 153.6, 210.6, 339.1, 531.5, 407.0, 452.0, 621.5, 571.5, 405.5, 418.4, 404.8, 434.2, 502.3, 365.6, 313.0, 592.3, 636.8, 743.5, 622.3, 790.7, 781.1, 788.9, 687.1, 855.7, 874.0, 996.5, 1002.3, 673.1, 663.0],
    [960.5, 971.5, 474.8, 405.9, 161.6, 129.0, 963.1, 1054.9, 871.8, 979.9, 839.8, 907.7, 689.2, 604.1, 583.2, 452.2, 394.5, 457.3, 220.9, 188.2, 212.6, 0.0, 57.9, 302.5, 238.7, 531.9, 546.3, 481.3, 583.0, 626.0, 345.3, 567.9, 716.0, 771.1, 867.1, 667.8, 925.0, 980.3, 923.1, 850.6, 979.3, 997.6, 1120.1, 946.1, 416.0, 470.5],
    [429.1, 568.2, 421.8, 408.2, 420.0, 445.1, 586.0, 653.4, 510.3, 538.1, 284.8, 352.7, 426.1, 358.2, 413.6, 418.6, 448.9, 258.3, 569.9, 358.4, 562.8, 557.9, 602.9, 647.1, 666.7, 33.3, 31.4, 106.1, 28.0, 130.0, 230.6, 170.0, 220.0, 246.1, 371.2, 250.0, 400.0, 455.3, 398.2, 295.6, 483.4, 501.7, 624.2, 630.0, 433.2, 331.2],
    [575.3, 714.4, 608.9, 595.2, 580.6, 605.7, 732.2, 799.6, 656.6, 684.3, 431.0, 498.9, 613.2, 545.3, 600.7, 605.7, 636.0, 445.4, 730.6, 519.1, 583.6, 718.5, 763.5, 667.9, 702.6, 187.8, 196.2, 256.0, 243.2, 113.1, 371.8, 357.1, 0.0, 133.4, 140.8, 121.5, 287.1, 342.4, 252.6, 262.5, 296.5, 314.9, 437.4, 443.2, 415.4, 325.6],
    [449.8, 588.9, 771.4, 791.1, 785.7, 810.8, 606.7, 674.1, 531.0, 558.8, 305.4, 318.0, 614.2, 611.2, 689.7, 768.3, 831.8, 641.2, 935.6, 724.1, 859.3, 923.6, 968.6, 943.6, 978.3, 395.0, 378.5, 470.3, 390.0, 352.4, 596.3, 552.9, 285.3, 157.6, 326.7, 397.1, 0.0, 99.3, 99.5, 136.9, 289.0, 265.5, 540.8, 671.4, 691.0, 601.3],
    [732.4, 871.5, 870.4, 856.7, 842.1, 867.2, 889.3, 956.7, 813.6, 841.4, 588.1, 600.6, 874.6, 806.7, 862.1, 867.2, 897.4, 706.8, 992.0, 780.5, 777.9, 980.0, 1025.0, 862.2, 896.9, 449.3, 457.7, 517.5, 504.6, 405.4, 633.3, 618.5, 296.1, 298.9, 125.1, 317.8, 284.9, 383.2, 196.3, 419.5, 0.0, 32.1, 279.8, 410.5, 609.7, 519.9],
    [927.6, 1066.7, 1011.3, 997.6, 886.0, 1008.1, 1084.5, 1151.9, 1008.8, 1036.6, 783.2, 851.2, 1015.5, 947.6, 1003.0, 1008.1, 1038.3, 847.7, 1132.9, 921.5, 829.4, 1038.1, 1091.4, 882.1, 948.4, 590.2, 598.6, 658.4, 645.5, 546.3, 774.2, 759.4, 437.0, 485.7, 313.8, 429.9, 578.8, 677.1, 490.2, 614.7, 329.2, 316.8, 70.6, 99.1, 588.5, 632.0],
    [859.5, 998.6, 685.5, 671.8, 264.1, 458.0, 1016.4, 1083.8, 940.8, 968.6, 715.2, 783.1, 727.2, 659.3, 714.7, 682.3, 712.6, 521.9, 614.5, 373.4, 207.8, 416.6, 469.8, 234.1, 326.8, 402.4, 420.6, 363.9, 458.4, 395.0, 308.2, 542.4, 414.2, 538.0, 497.6, 292.1, 691.7, 747.0, 657.2, 667.0, 609.8, 628.1, 651.0, 497.7, 0.0, 92.3],
]
# Candidate sites: fixed cost (thousand EUR/year, invented) and road travel time
# (h) to local warehouses 1 to 12 (OSRM, 10/11/2026)
SITES = [
    ("Barcelona", 560, [1.29, 1.31, 4.03, 11.07, 6.6, 10.79, 6.47, 7.99, 6.61, 9.79, 11.85, 11.06]),
    ("Getafe", 520, [7.69, 6.09, 4.01, 5.68, 4.58, 5.9, 0.68, 2.47, 4.63, 5.17, 6.66, 4.31]),
    ("Zaragoza", 430, [4.47, 2.87, 3.82, 9.36, 6.31, 9.57, 3.4, 4.92, 3.54, 6.73, 8.78, 7.99]),
    ("Valencia", 470, [4.88, 2.87, 0.0, 7.29, 2.63, 6.82, 4.07, 6.25, 6.72, 8.95, 10.45, 7.62]),
    ("Seville", 440, [11.92, 9.91, 7.31, 0.0, 6.24, 2.68, 6.15, 6.26, 9.25, 8.43, 9.66, 2.63]),
    ("Antequera", 360, [11.32, 9.31, 6.54, 2.03, 4.5, 0.81, 5.92, 7.74, 9.89, 10.32, 11.55, 4.52]),
    ("Valladolid", 400, [8.83, 7.24, 6.33, 6.33, 6.91, 8.24, 2.87, 0.0, 3.25, 3.35, 4.85, 4.81]),
    ("León", 350, [9.23, 7.64, 7.71, 7.17, 8.29, 9.62, 4.25, 2.04, 3.65, 1.55, 3.54, 5.65]),
]
# Road distance (km) between local warehouse 2 (Tarragona) and its six retailers,
# from the node of each row to the node of each column (OSRM, 10/11/2026)
ROUTE_NODES = [0, 1, 2, 7, 9, 11, 12]   # 0 = local warehouse 2; the others, retailer numbers
ROUTE_KM = [
    [0.0, 97.0, 104.7, 96.4, 0.0, 234.7, 213.3],
    [97.5, 0.0, 143.0, 156.0, 97.5, 153.0, 117.6],
    [105.6, 142.0, 0.0, 27.4, 105.6, 296.8, 258.8],
    [97.1, 158.3, 28.0, 0.0, 97.1, 313.9, 275.1],
    [0.0, 97.0, 104.7, 96.4, 0.0, 234.7, 213.3],
    [235.6, 154.4, 293.5, 311.3, 235.6, 0.0, 74.6],
    [208.9, 113.1, 254.0, 267.0, 208.9, 74.9, 0.0],
]

ROAD_RATE = 0.010          # transport rate of road of M3 (EUR/(bike*km))
MAX_TIME = 4               # maximum travel time from a regional to a local warehouse (h)
WEEKS = 52                 # weekly orders: the yearly orders divided by 52, rounded
VAN = 40                   # capacity of the van (bikes)
MAX_KM = 600               # longest distance of a route, a working day (km)
FIXED, PER_KM = 150, 0.60  # cost of a route: EUR per route plus EUR per km

R = range(1, len(RETAILERS) + 1)          # retailer numbers
L = range(1, len(LOCAL) + 1)              # local warehouse numbers


def orders(population):
    """Yearly orders (bikes/year): 600 for a city of 150.000 inhabitants, times the
    square root of the population over 150.000, rounded to ten bikes."""
    return int(10 * round(600 * (population / 150000) ** 0.5 / 10))


d = {r: orders(RETAILERS[r - 1][1]) for r in R}
K = {l: LOCAL[l - 1][1] for l in L}
cost = {(l, r): round(ROAD_KM[l - 1][r - 1] * ROAD_RATE, 2) for l in L for r in R}


# ---------------------------------------------------------------------------
# Output in European format: point for thousands, comma for decimals
# ---------------------------------------------------------------------------

def eu(x, decimals=2):
    return f"{x:,.{decimals}f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def retailer(r):
    return f"Retailer {r} ({RETAILERS[r - 1][0]})"


def local(l):
    return f"Local warehouse {l} ({LOCAL[l - 1][0]})"


def solve(model):
    result = model.solve(pulp.HiGHS(msg=False, gapRel=0, gapAbs=0))
    return getattr(result, "status", result) == 1      # PuLP 3: a number; PuLP 4: an object


def binary(model, name):
    # In PuLP 4 cat="Binary" drops the bounds 0 and 1; written as an integer in [0, 1]
    return model.add_variable(name, lowBound=0, upBound=1, cat="Integer")


def only_one(model, variables, best):
    """True if no other choice of the binary variables has the optimal cost."""
    chosen = [v for v in variables if v.value() > 0.5]
    others = [v for v in variables if v.value() <= 0.5]
    model += pulp.lpSum(chosen) - pulp.lpSum(others) <= len(chosen) - 1
    return not solve(model) or pulp.value(model.objective) > best + 0.005


# ---------------------------------------------------------------------------
# §3 Which local warehouse serves each retailer
# ---------------------------------------------------------------------------

def plan_of(warehouse):
    load = {l: sum(d[r] for r in R if warehouse[r] == l) for l in L}
    return {"warehouse": warehouse, "load": load, "cost": sum(cost[warehouse[r], r] * d[r] for r in R)}


def cheapest():
    return plan_of({r: min(L, key=lambda l: cost[l, r]) for r in R})


def rule():
    room, warehouse = dict(K), {}
    for r in R:                                   # in the order of the list
        fits = [l for l in L if room[l] >= d[r]]
        warehouse[r] = min(fits, key=lambda l: cost[l, r])
        room[warehouse[r]] -= d[r]
    return plan_of(warehouse)


def assignment(split=False):
    model = pulp.LpProblem("generalized_assignment", pulp.LpMinimize)
    x = {(l, r): (model.add_variable(f"x_{l}_{r}", lowBound=0, upBound=1) if split else binary(model, f"x_{l}_{r}"))
         for l in L for r in R}
    total = pulp.lpSum(cost[l, r] * d[r] * x[l, r] for l in L for r in R)
    model += total
    for r in R:
        model += pulp.lpSum(x[l, r] for l in L) == 1                 # one local warehouse
    for l in L:
        model += pulp.lpSum(d[r] * x[l, r] for r in R) <= K[l]      # node capacity
    solve(model)
    share = {key: v.value() for key, v in x.items()}
    plan = {"cost": pulp.value(model.objective), "share": share,
            "load": {l: sum(d[r] * share[l, r] for r in R) for l in L}}
    if split:
        # With the cost fixed at its optimum, every share has the same minimum and maximum
        model += total <= plan["cost"] + 1e-6
        ends = []
        for v in x.values():
            for sense in (pulp.LpMinimize, pulp.LpMaximize):
                model.sense = sense
                model.setObjective(v)
                solve(model)
                ends.append(v.value())
        plan["only"] = all(abs(a - b) < 1e-6 for a, b in zip(ends[::2], ends[1::2]))
    else:
        plan["warehouse"] = {r: l for (l, r), v in share.items() if v > 0.5}
        plan["only"] = only_one(model, list(x.values()), plan["cost"])
    return plan


# ---------------------------------------------------------------------------
# §4 Which candidate sites act as regional warehouses
# ---------------------------------------------------------------------------

def reach(max_time=MAX_TIME):
    return {n: [l for l in L if times[l - 1] <= max_time] for n, _, times in SITES}


def covering(exactly_one=False, max_time=MAX_TIME):
    sets = reach(max_time)
    model = pulp.LpProblem("set_covering", pulp.LpMinimize)
    y = {n: binary(model, f"y_{n}") for n in sets}
    model += pulp.lpSum(c * y[n] for n, c, _ in SITES)
    for l in L:
        reached = pulp.lpSum(y[n] for n in sets if l in sets[n])
        model += (reached == 1) if exactly_one else (reached >= 1)
    if not solve(model):
        return None
    chosen = [n for n in sets if y[n].value() > 0.5]
    best = pulp.value(model.objective)
    return {"sites": chosen, "cost": best, "sets": sets, "only": only_one(model, list(y.values()), best)}


# ---------------------------------------------------------------------------
# §5 The weekly routes of local warehouse 2
# ---------------------------------------------------------------------------

week = {r: round(d[r] / WEEKS) for r in ROUTE_NODES[1:]}


def candidate_routes(van=VAN, max_stops=None):
    where = {node: k for k, node in enumerate(ROUTE_NODES)}
    routes = []
    for size in range(1, (max_stops or len(week)) + 1):
        for group in itertools.combinations(ROUTE_NODES[1:], size):
            load = sum(week[r] for r in group)
            if load > van:
                continue
            best = None
            for order in itertools.permutations(group):        # every order of visits
                stops = [0, *order, 0]
                km = round(sum(ROUTE_KM[where[a]][where[b]] for a, b in zip(stops, stops[1:])), 1)
                if best is None or km < best[0]:
                    best = (km, order)
            if best[0] <= MAX_KM:
                routes.append({"stops": best[1], "km": best[0], "load": load, "cost": round(FIXED + PER_KM * best[0], 2)})
    for k, route in enumerate(routes, 1):
        route["number"] = k
    return routes


def partition(routes, exactly_one=True):
    model = pulp.LpProblem("set_partitioning", pulp.LpMinimize)
    y = {route["number"]: binary(model, f"y_{route['number']}") for route in routes}
    model += pulp.lpSum(route["cost"] * y[route["number"]] for route in routes)
    for r in week:
        visits = pulp.lpSum(y[route["number"]] for route in routes if r in route["stops"])
        model += (visits == 1) if exactly_one else (visits >= 1)
    if not solve(model):
        return None
    chosen = [route for route in routes if y[route["number"]].value() > 0.5]
    best = pulp.value(model.objective)
    return {"routes": chosen, "cost": best, "only": only_one(model, list(y.values()), best)}


def route_name(route):
    """The retailers of a route in the order of visits; the route leaves local
    warehouse 2 and returns to it."""
    return ", ".join(RETAILERS[r - 1][0] for r in route["stops"])


# ---------------------------------------------------------------------------
# Tables of the document
# ---------------------------------------------------------------------------

def main():
    print("Table 1. Retailers: population and yearly orders d_r")
    for r in R:
        print(f"  {retailer(r):<40}{eu(RETAILERS[r - 1][1], 0):>12}{eu(d[r], 0):>8}")
    print(f"  {'Total':<40}{'':>12}{eu(sum(d.values()), 0):>8}")
    print("\nTable 2. Local warehouses: node capacity K^n_l (bikes/year)")
    for l in L:
        print(f"  {local(l):<44}{eu(K[l], 0):>8}")
    print(f"  {'Total':<44}{eu(sum(K.values()), 0):>8}   ({eu(100 * (sum(K.values()) / sum(d.values()) - 1), 1)} % "
          f"above the orders)")
    print("\nTable 3. Road distance (km) from each local warehouse (columns 1 to 12) to each retailer")
    for r in R:
        print(f"  {retailer(r):<40}" + "".join(f"{eu(ROAD_KM[l - 1][r - 1], 1):>8}" for l in L))

    plans = {"Cheapest": cheapest(), "Rule": rule(), "Generalized assignment": assignment(),
             "Transportation problem": assignment(split=True)}
    gap, split = plans["Generalized assignment"]["cost"], plans["Transportation problem"]["cost"]
    print("\nTable 5. Cost of each plan (EUR/year)")
    for name, plan in plans.items():
        over = [l for l in L if plan["load"][l] > K[l] + 1e-6]
        note = f"not valid: {', '.join(local(l) for l in over)} over capacity" if over else "valid"
        print(f"  {name:<26}{eu(plan['cost']):>12}   {eu(100 * (plan['cost'] / gap - 1), 1):>6} %   {note}")
    print(f"  The generalized assignment is the only optimal plan: {plans['Generalized assignment']['only']}; "
          f"the transportation problem: {plans['Transportation problem']['only']}")
    print("\nTable 6. Load of each local warehouse (bikes/year): capacity, then each plan")
    for l in L:
        print(f"  {local(l):<44}{eu(K[l], 0):>8}" + "".join(f"{eu(p['load'][l], 1):>10}" for p in plans.values()))
    print("\nTable 7. Retailers not served by their cheapest local warehouse in some plan: orders, then the local "
          "warehouse in each plan")
    base = plans["Cheapest"]["warehouse"]
    for r in R:
        model_l = plans["Generalized assignment"]["warehouse"][r]
        shares = {l: s for l, s in ((l, plans["Transportation problem"]["share"][l, r]) for l in L) if s > 1e-6}
        rule_l = plans["Rule"]["warehouse"][r]
        if model_l == base[r] and rule_l == base[r] and shares == {base[r]: 1}:
            continue
        split_text = "; ".join(f"{LOCAL[l - 1][0]} {eu(100 * s, 1)} %" for l, s in shares.items())
        print(f"  {retailer(r):<24}{eu(d[r], 0):>6}  {LOCAL[base[r] - 1][0]:<24}{LOCAL[rule_l - 1][0]:<24}"
              f"{LOCAL[model_l - 1][0]:<24}{split_text}")

    print("\nTable 8. Candidate sites: fixed cost c^F_n (thousand EUR/year) and travel time (h) to local "
          "warehouses 1 to 12")
    for n, c, times in SITES:
        print(f"  {n:<12}{c:>6}" + "".join(f"{eu(t):>7}" for t in times))
    cover = covering()
    print(f"\nTable 9. Local warehouses within {MAX_TIME} h of each candidate site")
    for n, s in cover["sets"].items():
        mark = "chosen" if n in cover["sites"] else ""
        print(f"  {n:<12}{mark:<8}" + "; ".join(LOCAL[l - 1][0] for l in s))
    print(f"  At least one: regional warehouses at {', '.join(cover['sites'])}; {eu(cover['cost'], 0)} thousand "
          f"EUR/year; the only optimal plan: {cover['only']}")
    twice = [l for l in L if sum(l in cover["sets"][n] for n in cover["sites"]) > 1]
    print(f"  Within reach of two chosen sites: {', '.join(local(l) for l in twice)}")
    print(f"  Exactly one: {'no feasible solution' if covering(exactly_one=True) is None else 'a solution'}")

    print("\nTable 10. Weekly orders of the retailers of local warehouse 2 (bikes)")
    for r, q in week.items():
        print(f"  {retailer(r):<34}{q:>4}")
    print("\nTable 11. Road distance (km) between local warehouse 2 and its retailers, from row to column")
    for a, row in zip(ROUTE_NODES, ROUTE_KM):
        print(f"  {(local(2) if a == 0 else retailer(a)):<34}" + "".join(f"{eu(v, 1):>8}" for v in row))
    routes = candidate_routes()
    print(f"\nTable 12. Candidate routes ({len(routes)}): load (bikes), distance (km) and cost (EUR)")
    for route in routes:
        print(f"  {route['number']:>3}  {route_name(route):<32}{route['load']:>4}{eu(route['km'], 1):>8}"
              f"{eu(route['cost']):>10}")
    print("\nTable 13. Weekly routes of least cost")
    for name, plan in (("Full list, exactly one (set partitioning)", partition(routes)),
                       ("Full list, at least one (set covering)", partition(routes, exactly_one=False)),
                       ("Short list, exactly one", partition([r for r in routes if len(r["stops"]) <= 2]))):
        print(f"  {name:<44}routes {'; '.join(str(r['number']) for r in plan['routes']):<12}"
              f"{eu(sum(r['km'] for r in plan['routes']), 1):>8} km{eu(plan['cost']):>10} EUR/week   "
              f"the only optimal plan: {plan['only']}")


if __name__ == "__main__":
    main()
