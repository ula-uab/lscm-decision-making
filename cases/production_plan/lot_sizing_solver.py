# Lot sizing at the plants
#
# This script reproduces every table of lot_sizing.md (same folder): the
# calendar (Tables 1 to 3); the orders of the retailers (Table 4); the
# stock at the plants (Table 5) and their assembly lines (Table 6); the plan of
# M4 solved with the orders of Table 4, and the least stock of each plant
# (Table 7); the product mix of the shipments (Table 8) and the shipments of
# each plant in each week (Table 9); the weekly lot plans of the three plants
# (Tables 10 to 12); the hours of the line by month (Table 13); and the runs of
# part d) (Tables 14 and 15). It also prints the numbers of the text that are in
# no table: the cost of M4, the setup and holding cost of each plant, the plan of
# step 7, and whether another plan has the same costs.
#
# The models are written with the PuLP library and solved by the HiGHS solver.
# M4 is the model of retailers.md, unchanged, solved with the orders of Table 4.
# Every quantity is computed as an exact fraction, and every rounding is half up
# from the exact value.
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
#     Windows:          python lot_sizing_solver.py
#     macOS and Linux:  python3 lot_sizing_solver.py
# It takes about half a minute.

import math
import sys
from fractions import Fraction

import pulp


# ---------------------------------------------------------------------------
# Data of M4 (retailers.md), unchanged except the orders of the retailers.
# Invented (2026), except the places and distances
# ---------------------------------------------------------------------------

T = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]        # months
F = ["Plant 1", "Plant 2", "Plant 3"]                 # assembly plants
CENTRAL, TERMINAL = "Central warehouse", "Rail terminal"
REGIONAL = ["Regional warehouse 1", "Regional warehouse 2"]
LOCAL = ["Local warehouse 1", "Local warehouse 2", "Local warehouse 3", "Local warehouse 4"]
RETAILERS = ["Retailer 1", "Retailer 2", "Retailer 3", "Retailer 4", "Retailer 5", "Retailer 6"]
NODES = F + [CENTRAL, TERMINAL] + REGIONAL + LOCAL + RETAILERS

# Place of each retailer (Nominatim, OpenStreetMap, consulted on 23/10/2026)
PLACES = {"Retailer 1": "Lleida", "Retailer 2": "Sabadell", "Retailer 3": "Alicante",
          "Retailer 4": "Murcia", "Retailer 5": "Córdoba", "Retailer 6": "Granada"}

# Unit assembly cost c[f] (EUR/bike) and assembly capacity K[f] (bikes/month)
c = {"Plant 1": 310, "Plant 2": 340, "Plant 3": 390}
K = {"Plant 1": 250, "Plant 2": 200, "Plant 3": 150}

# Holding cost c_h[i] (EUR/(bike*month)), storage capacity K_h[i] (bikes) and
# initial stock h_0[i] (bikes) of each node; the required final stock is the
# initial stock. The rail terminal and the retailers hold no stock
c_h = {"Plant 1": 5, "Plant 2": 6, "Plant 3": 7, CENTRAL: 8, TERMINAL: 0,
       "Regional warehouse 1": 9, "Regional warehouse 2": 10,
       "Local warehouse 1": 11, "Local warehouse 2": 12, "Local warehouse 3": 13, "Local warehouse 4": 14}
K_h = {"Plant 1": 40, "Plant 2": 30, "Plant 3": 20, CENTRAL: 150, TERMINAL: 0,
       "Regional warehouse 1": 60, "Regional warehouse 2": 60,
       "Local warehouse 1": 20, "Local warehouse 2": 20, "Local warehouse 3": 20, "Local warehouse 4": 20}
for r in RETAILERS:
    c_h[r], K_h[r] = 0, 0
h_0 = {i: {"Plant 1": 20, "Plant 2": 10}.get(i, 0) for i in NODES}

# Node capacity K_n[i]: bikes the node can receive in a month
K_n = {"Regional warehouse 2": 280}

# The network as a list of arcs: origin, destination, mode, distance (km) and
# arc capacity (bikes/month). Distances: OSRM (road) and OpenRailRouting (rail),
# on OpenStreetMap data, consulted on 23/10/2026. The transport cost of an arc
# is its distance times the rate of its mode, rounded to the cent (EUR/bike)
RATE = {"Road": 0.010, "Rail": 0.006}
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
ARCS = [(i, j, cap, round(km * RATE[mode], 2)) for i, j, mode, km, cap in NETWORK]

# Backorder share beta[r] of each retailer (the rest is lost sales), backorder
# cost c_b (EUR/(bike*month)) and lost-sale cost c_l (EUR/bike)
BETA = dict(zip(RETAILERS, [0.9, 0.7, 0.5, 0.8, 0.6, 0.4]))
c_b, c_l = 60, 700


# ---------------------------------------------------------------------------
# §1 Data of the weekly plans (Tables 1 to 6)
# ---------------------------------------------------------------------------

MODELS = ["City", "Trekking", "Mountain", "Cargo"]
WEEKS = list(range(1, 27))           # weeks from Monday to Sunday; week 1 starts on Monday 1 January
MONTH_DAYS = dict(zip(T, [31, 28, 31, 30, 31, 30]))
HOURS_PER_DAY = 8

# Holidays from Monday to Friday (month, day), Table 1
HOLIDAYS = {"Plant 1": [("Jan", 1), ("Mar", 29), ("Mar", 30), ("Apr", 2), ("May", 1)],
            "Plant 2": [("Jan", 1), ("Mar", 29), ("Mar", 30), ("Apr", 2), ("May", 1)],
            "Plant 3": [("Jan", 1), ("Mar", 12), ("Mar", 19), ("Mar", 30), ("Apr", 2), ("May", 1)]}

# The data with which the weekly orders are generated (the document gives the
# orders, not these data): average orders (bikes/month) and product mix of each
# retailer; seasonal index of each model; factor of each week
AVERAGE = dict(zip(RETAILERS, [65, 105, 85, 75, 95, 45]))
MIX = {r: dict(zip(MODELS, m)) for r, m in zip(RETAILERS, [
    ("0.25", "0.35", "0.35", "0.05"), ("0.50", "0.20", "0.10", "0.20"), ("0.45", "0.35", "0.10", "0.10"),
    ("0.50", "0.30", "0.10", "0.10"), ("0.50", "0.35", "0.10", "0.05"), ("0.25", "0.20", "0.50", "0.05")])}
SEASONAL = {"City": "0.7 0.9 0.9 1.2 1.2 1.1", "Trekking": "0.4 0.7 0.8 1.5 1.5 1.1",
            "Mountain": "0.3 0.6 0.7 1.7 1.7 1.0", "Cargo": "1.0 1.0 1.0 1.0 1.0 1.0"}
SEASONAL = {j: dict(zip(T, values.split())) for j, values in SEASONAL.items()}
FACTOR = dict(zip(WEEKS, "0.9 1.0 1.1 1.0 1.0 0.95 1.05 1.0 1.0 1.0 1.1 0.9 1.0 "
                         "0.9 1.0 1.05 1.05 1.0 0.95 1.05 1.0 1.0 1.0 1.05 0.95 1.0".split()))

# Initial and required final stock of each model at each plant (bikes), Table 5
STOCK_0 = {"Plant 1": dict(zip(MODELS, [11, 4, 2, 3])), "Plant 2": dict(zip(MODELS, [5, 2, 1, 2])),
           "Plant 3": dict(zip(MODELS, [0, 0, 0, 0]))}

# Assembly time (h/bike) and setup time (h/setup) at each plant, Table 6
ASSEMBLY = {"Plant 1": "0.42 0.52 0.71 0.90", "Plant 2": "0.525 0.65 0.8875 1.125", "Plant 3": "0.70 0.867 1.183 1.50"}
SETUP = {"Plant 1": "2 2 3 4", "Plant 2": "2.5 2.5 3.75 5", "Plant 3": "3 3 4.5 6"}
ASSEMBLY = {f: dict(zip(MODELS, map(Fraction, v.split()))) for f, v in ASSEMBLY.items()}
SETUP = {f: dict(zip(MODELS, map(Fraction, v.split()))) for f, v in SETUP.items()}

# Setup cost: 40 EUR/h of the changeover crew times the setup time, plus 20 EUR
# for the check of the first bike. Holding cost: that of M4 times 12/52 times a
# factor of each model, rounded to the cent (EUR/(bike*week))
VALUE_FACTOR = dict(zip(MODELS, map(Fraction, ["0.8", "1.0", "1.2", "1.4"])))


def half_up(x, decimals=0):
    """x rounded half up from its exact value."""
    scale = 10 ** decimals
    return Fraction(math.floor(Fraction(x) * scale + Fraction(1, 2)), scale)


def setup_cost(setup):
    return {j: 40 * setup[j] + 20 for j in MODELS}


def holding_cost(f):
    return {j: half_up(c_h[f] * Fraction(12, 52) * VALUE_FACTOR[j], 2) for j in MODELS}


def cumulative(values):
    """Whole numbers whose sums from the first are the sums of values rounded
    half up."""
    out, total, before = [], Fraction(0), 0
    for v in values:
        total += v
        now = int(half_up(total))
        out.append(now - before)
        before = now
    return out


def largest_remainder(total, share):
    """total split in whole numbers in proportion to share, keeping the total."""
    raw = {j: total * share[j] for j in MODELS}
    out = {j: math.floor(raw[j]) for j in MODELS}
    for j in sorted(MODELS, key=lambda j: raw[j] - out[j], reverse=True)[:total - sum(out.values())]:
        out[j] += 1
    return out


def share(values):
    total = sum(values.values())
    return {j: Fraction(values[j]) / total for j in values}


# Calendar: the month of each day from Monday to Friday of each week
def month_of(day):
    for t in T:
        if day < MONTH_DAYS[t]:
            return t
        day -= MONTH_DAYS[t]


def day_number(t, day):
    return sum(MONTH_DAYS[s] for s in T[:T.index(t)]) + day - 1


WEEK_MONTHS = {w: [month_of(7 * (w - 1) + k) for k in range(5)] for w in WEEKS}
n = {(w, t): WEEK_MONTHS[w].count(t) for w in WEEKS for t in T}           # days of week w in month t
N = {t: sum(n[w, t] for w in WEEKS) for t in T}                            # days of month t
PLAN_WEEKS = {t: [w for w in WEEKS if max(T, key=WEEK_MONTHS[w].count) == t] for t in T}


def available_capacity(f, holidays=HOLIDAYS):
    """K_w: working days of each week times 8 h."""
    off = {day_number(t, d) for t, d in holidays[f]}
    return {w: HOURS_PER_DAY * sum(1 for k in range(5) if 7 * (w - 1) + k not in off) for w in WEEKS}


# ---------------------------------------------------------------------------
# §1 Orders of the retailers (§1.2 and §1.3 of the document: Table 4)
# ---------------------------------------------------------------------------

weekly = {}
for r in RETAILERS:
    for j in MODELS:
        raw = [AVERAGE[r] * Fraction(MIX[r][j]) * sum(Fraction(SEASONAL[j][t]) for t in WEEK_MONTHS[w]) / 5
               * Fraction(12, 52) * Fraction(FACTOR[w]) for w in WEEKS]
        weekly.update({(r, j, w): q for w, q in zip(WEEKS, cumulative(raw))})
by_model = {(r, j, t): sum(Fraction(n[w, t], 5) * weekly[r, j, w] for w in WEEKS)
            for r in RETAILERS for j in MODELS for t in T}
orders = {}
for r in RETAILERS:
    raw = [sum(by_model[r, j, t] for j in MODELS) for t in T]
    orders.update({(r, t): q for t, q in zip(T, cumulative(raw))})
SIX_MONTH_MIX = share({j: sum(weekly[r, j, w] for r in RETAILERS for w in WEEKS) for j in MODELS})


# ---------------------------------------------------------------------------
# §2 The master plan: M4, solved with the orders of Table 4
# ---------------------------------------------------------------------------

def solve_m4(order):
    """The model of retailers.md (M4) with the orders of each retailer in each
    month. Returns its cost and the values of its variables, or None."""
    model = pulp.LpProblem("retailers", pulp.LpMinimize)
    key = lambda node: node.replace(" ", "")      # noqa: E731
    A = range(len(ARCS))
    p = {(f, t): model.add_variable(f"p_{key(f)}_{t}", lowBound=0) for f in F for t in T}
    x = {(a, t): model.add_variable(f"x_{a}_{t}", lowBound=0) for a in A for t in T}
    h = {(i, t): model.add_variable(f"h_{key(i)}_{t}", lowBound=0) for i in NODES for t in T}
    s = {(r, t): model.add_variable(f"s_{key(r)}_{t}", lowBound=0) for r in RETAILERS for t in T}
    b = {(r, t): model.add_variable(f"b_{key(r)}_{t}", lowBound=0) for r in RETAILERS for t in T}
    l = {(r, t): model.add_variable(f"l_{key(r)}_{t}", lowBound=0) for r in RETAILERS for t in T}
    model += (pulp.lpSum(c[f] * p[f, t] for f in F for t in T)
              + pulp.lpSum(c_h[i] * h[i, t] for i in NODES for t in T)
              + pulp.lpSum(ARCS[a][3] * x[a, t] for a in A for t in T)
              + pulp.lpSum(c_b * b[r, t] + c_l * l[r, t] for r in RETAILERS for t in T))
    for i in NODES:
        into = [a for a in A if ARCS[a][1] == i]
        out = [a for a in A if ARCS[a][0] == i]
        for k, t in enumerate(T):
            before = h_0[i] if k == 0 else h[i, T[k - 1]]
            assembled = p[i, t] if i in F else 0
            delivered = s[i, t] if i in RETAILERS else 0
            arriving = pulp.lpSum(x[a, t] for a in into)
            shipped = pulp.lpSum(x[a, t] for a in out)
            model += (before + assembled + arriving == shipped + delivered + h[i, t], f"balance_{key(i)}_{t}")
            model += (shipped + delivered <= before + assembled + arriving, f"shipment_limit_{key(i)}_{t}")
            model += (h[i, t] <= K_h[i], f"storage_{key(i)}_{t}")
            if i in K_n:
                model += (arriving <= K_n[i], f"node_capacity_{key(i)}_{t}")
        model += (h[i, T[-1]] >= h_0[i], f"final_stock_{key(i)}")
    for r in RETAILERS:
        for k, t in enumerate(T):
            before = 0 if k == 0 else b[r, T[k - 1]]
            model += (s[r, t] + b[r, t] + l[r, t] - before == order[r, t], f"backorders_{key(r)}_{t}")
            if k < len(T) - 1:
                model += (b[r, t] == BETA[r] * (before + order[r, t] - s[r, t]), f"backorder_share_{key(r)}_{t}")
        model += (b[r, T[-1]] == 0, f"backorders_at_the_end_{key(r)}")
    for a in A:
        for t in T:
            model += (x[a, t] <= ARCS[a][2], f"arc_capacity_{a}_{t}")
    for f in F:
        for t in T:
            model += (p[f, t] <= K[f], f"capacity_{key(f)}_{t}")
    # PuLP 3 returns the status as a number and PuLP 4 as an object with a
    # field status; 1 is optimal in both
    result = model.solve(pulp.HiGHS(msg=False))
    if getattr(result, "status", result) != 1:
        return None
    exact = lambda v: Fraction(round(v.value() * 1000), 1000)      # noqa: E731  (to the thousandth of a bike)
    values = {kind: {k: exact(v) for k, v in var.items()}
              for kind, var in (("p", p), ("x", x), ("h", h), ("s", s), ("b", b), ("l", l))}
    return pulp.value(model.objective), values


# ---------------------------------------------------------------------------
# §2 Shipments and least stock of each plant (§2.2 of the document)
# ---------------------------------------------------------------------------

def from_master_plan(v):
    """The product mix of the shipments, the split of the seasonal stock, the
    least stock and the weekly shipments of each plant, from the plan of M4."""
    shipped = {(f, t): sum(v["x"][a, t] for a in range(len(ARCS)) if ARCS[a][0] == f) for f in F for t in T}
    network = {t: sum(v["h"][i, t] for i in NODES) for t in T}
    warehouses = {t: network[t] - sum(v["h"][f, t] for f in F) for t in T}
    # Seasonal stock: split with the orders of the months in which it is used
    split = {}
    for k, t in enumerate(T):
        used = []
        for m in range(k + 1, len(T)):
            if network[T[m]] < network[T[m - 1]]:
                used.append(T[m])
            elif used:
                break
        split[t] = (share({j: sum(by_model[r, j, m] for r in RETAILERS for m in used) for j in MODELS}) if used
                    else share({j: sum(STOCK_0[f][j] for f in F) for j in MODELS}))
    # What the retailers receive, by model: backorders first, each bike with the
    # product mix of the month in which it was ordered
    delivered = {(j, t): Fraction(0) for j in MODELS for t in T}
    for r in RETAILERS:
        pending = []
        for t in T:
            pending.append([orders[r, t], t])
            left, lost = v["s"][r, t], v["l"][r, t]
            for item in pending:
                served = min(item[0], left)
                mix = share({j: by_model[r, j, item[1]] for j in MODELS})
                for j in MODELS:
                    delivered[j, t] += served * mix[j]
                item[0] -= served
                left -= served
            for item in pending:
                gone = min(item[0], lost)
                item[0] -= gone
                lost -= gone
            pending = [item for item in pending if item[0] > 0]
    # Product mix of the shipments: deliveries plus the change in the stock of
    # the warehouses, split as the seasonal stock
    mix = {}
    for k, t in enumerate(T):
        before = {j: 0 for j in MODELS} if k == 0 else {j: warehouses[T[k - 1]] * split[T[k - 1]][j] for j in MODELS}
        mix[t] = share({j: delivered[j, t] + warehouses[t] * split[t][j] - before[j] for j in MODELS})
    least = {(f, t): dict(STOCK_0[f]) if t == T[-1] else largest_remainder(int(v["h"][f, t]), split[t])
             for f in F for t in T}
    x = {}
    for f in F:
        for j in MODELS:
            raw = [sum(Fraction(n[w, t], N[t]) * shipped[f, t] * mix[t][j] for t in T) for w in WEEKS]
            x.update({(f, j, w): q for w, q in zip(WEEKS, cumulative(raw))})
    return {"shipped": shipped, "network": network, "split": split, "mix": mix, "least": least, "x": x}


def same_mix(x, least):
    """Part d): the bikes that each plant ships in a week split with the product
    mix of the six months; the least stock split in the same proportions, except
    at the end of June."""
    out = {}
    for f in F:
        for j in MODELS:
            raw = [sum(x[f, i, w] for i in MODELS) * SIX_MONTH_MIX[j] for w in WEEKS]
            out.update({(f, j, w): q for w, q in zip(WEEKS, cumulative(raw))})
    h_min = {(f, t): dict(STOCK_0[f]) if t == T[-1] else largest_remainder(sum(least[f, t].values()), SIX_MONTH_MIX)
             for f in F for t in T}
    return out, h_min


# ---------------------------------------------------------------------------
# §3 The weekly lot plan of a plant: one model for each month (steps 4 to 6)
# ---------------------------------------------------------------------------

def solver():
    """HiGHS, solving to the exact optimum: no relative or absolute gap."""
    return pulp.HiGHS(msg=False, gapRel=0, gapAbs=0)


def optimal(result):
    return getattr(result, "status", result) == 1


def month_plan(weeks, x, h_min, h_start, a, a_set, c_set, c_hold, k_h, k_w):
    """The plan of one month: stage 1, least capacity overload; stage 2, least
    setup and holding cost among the plans with that capacity overload. Returns
    the bikes assembled and the setups, and whether another plan has the same
    costs; None if it has no plan."""
    model = pulp.LpProblem("lot_sizing", pulp.LpMinimize)
    p = {(j, w): model.add_variable(f"p_{j}_{w}", lowBound=0, cat="Integer") for j in MODELS for w in weeks}
    h = {(j, w): model.add_variable(f"h_{j}_{w}", lowBound=0, cat="Integer") for j in MODELS for w in weeks}
    d = {(j, w): model.add_variable(f"delta_{j}_{w}", lowBound=0, upBound=1, cat="Integer")
         for j in MODELS for w in weeks}
    o = {w: model.add_variable(f"o_{w}", lowBound=0) for w in weeks}
    for j in MODELS:
        for k, w in enumerate(weeks):
            before = h_start[j] if k == 0 else h[j, weeks[k - 1]]
            # Balance between periods; only if: assembled only if set up
            model += (before + p[j, w] == x[j, w] + h[j, w], f"balance_{j}_{w}")
            model += (p[j, w] <= (x[j, w] + k_h) * d[j, w], f"setup_{j}_{w}")
        # Least stock at the end of the month
        model += (h[j, weeks[-1]] >= h_min[j], f"least_stock_{j}")
    for w in weeks:
        # Capacity of the line, relaxed by the capacity overload; storage capacity
        model += (pulp.lpSum(float(a[j]) * p[j, w] + float(a_set[j]) * d[j, w] for j in MODELS) <= k_w[w] + o[w],
                  f"capacity_{w}")
        model += (pulp.lpSum(h[j, w] for j in MODELS) <= k_h, f"storage_{w}")
    # Stage 1: least capacity overload
    model += pulp.lpSum(o.values())
    if not optimal(model.solve(solver())):
        return None
    model += (pulp.lpSum(o.values()) <= pulp.value(model.objective) + 1e-6, "least_overload")
    # Stage 2: least setup and holding cost
    cost = pulp.lpSum(float(c_set[j]) * d[j, w] + float(c_hold[j]) * h[j, w] for j in MODELS for w in weeks)
    model.setObjective(cost)
    model.solve(solver())
    plan = {k: round(v.value()) for k, v in p.items()}
    setups = {k: round(v.value()) for k, v in d.items()}
    # Another plan with the same costs: the one that differs most from this one
    model += (cost <= pulp.value(model.objective) + 1e-6, "least_cost")
    gaps = []
    for (j, w), var in p.items():
        bound = x[j, w] + k_h
        z = model.add_variable(f"z_{j}_{w}", lowBound=0, upBound=1, cat="Integer")
        g = model.add_variable(f"g_{j}_{w}", lowBound=0)
        model += (g <= var - plan[j, w] + bound * (1 - z), f"gap_up_{j}_{w}")
        model += (g <= plan[j, w] - var + bound * z, f"gap_down_{j}_{w}")
        gaps.append(g)
    model.sense = pulp.LpMaximize
    model.setObjective(pulp.lpSum(gaps))
    other = optimal(model.solve(solver())) and pulp.value(model.objective) > 0.5
    return plan, setups, other


def week_row(stock, assembled, setups, a, a_set, k):
    hours = sum(a[j] * assembled[j] for j in MODELS)
    setup_hours = sum(a_set[j] * setups[j] for j in MODELS)
    return {"available": Fraction(k), "assembled": assembled, "stock": stock, "setups": setups,
            "assembly": hours, "setup hours": setup_hours, "overload": max(Fraction(0), hours + setup_hours - k),
            "spare": max(Fraction(0), k - hours - setup_hours)}


def weekly_plan(f, x, least, a=None, a_set=None, k_w=None, lot_for_lot=False):
    """The plans of the six months of plant f, one after the other. With
    lot_for_lot, the plan of step 7: each week assembles what it ships less the
    stock it holds, and in the week of the end of the month also what it lacks of
    the least stock."""
    a, a_set, k_w = a or ASSEMBLY[f], a_set or SETUP[f], k_w or available_capacity(f)
    c_set, c_hold = setup_cost(a_set), holding_cost(f)
    stock, weeks, others = dict(STOCK_0[f]), {}, []
    for t, plan_weeks in PLAN_WEEKS.items():
        xs = {(j, w): x[f, j, w] for j in MODELS for w in plan_weeks}
        if not lot_for_lot:
            plan, setups, other = month_plan(plan_weeks, xs, least[f, t], stock, a, a_set, c_set, c_hold, K_h[f], k_w)
            if other:
                others.append(t)
        for w in plan_weeks:
            if lot_for_lot:
                need = {j: xs[j, w] + (least[f, t][j] if w == plan_weeks[-1] else 0) for j in MODELS}
                assembled = {j: max(0, need[j] - stock[j]) for j in MODELS}
                set_up = {j: int(assembled[j] > 0) for j in MODELS}
            else:
                assembled = {j: plan[j, w] for j in MODELS}
                set_up = {j: setups[j, w] for j in MODELS}
            stock = {j: stock[j] + assembled[j] - xs[j, w] for j in MODELS}
            weeks[w] = week_row(stock, assembled, set_up, a, a_set, k_w[w])
    cost = sum(c_set[j] * r["setups"][j] + c_hold[j] * r["stock"][j] for r in weeks.values() for j in MODELS)
    return weeks, cost, others


def by_month(weeks, key):
    return {t: sum(weeks[w][key] for w in plan_weeks) for t, plan_weeks in PLAN_WEEKS.items()}


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def eu(x, decimals=2):
    """A number in European format, rounded half up from its exact value."""
    x = half_up(x, decimals)
    text = f"{float(x):,.{decimals}f}".replace(",", " ").replace(".", ",").replace(" ", ".")
    return "0" + text[2:] if text.startswith("-0") and not text.strip("-0,") else text


def bikes(values):
    return "; ".join(str(values[j]) for j in MODELS)


def title(text):
    print()
    print(text)
    print("=" * len(text))


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

    title("§1 Data")
    print("Tables 1 to 3. Working days and available capacity of each week (h)")
    capacity = {f: available_capacity(f) for f in F}
    print(f"{'Week':<6}" + "".join(f"{f:>16}" for f in F))
    for w in WEEKS:
        if any(capacity[f][w] < 40 for f in F):
            print(f"{w:<6}" + "".join(f"{f'{capacity[f][w] // 8} days, {capacity[f][w]} h':>16}" for f in F))
    print("Every other week: 5 days, 40 h. Days from Monday to Friday of each month: "
          + "; ".join(f"{t} {N[t]}" for t in T))
    print()
    totals = {j: sum(weekly[r, j, w] for r in RETAILERS for w in WEEKS) for j in MODELS}
    print("Orders of the 26 weeks, all retailers: " + "; ".join(f"{j} {eu(totals[j], 0)}" for j in MODELS)
          + "; product mix " + "; ".join(f"{eu(100 * SIX_MONTH_MIX[j], 1)} %" for j in MODELS))
    print()
    print("Table 4. Orders of each retailer in each month (bikes)")
    print(f"{'':<24}" + "".join(f"{t:>7}" for t in T) + f"{'Six months':>12}")
    for r in RETAILERS:
        print(f"{r + ' (' + PLACES[r] + ')':<24}" + "".join(f"{orders[r, t]:>7}" for t in T)
              + f"{sum(orders[r, t] for t in T):>12}")
    print(f"{'All':<24}" + "".join(f"{sum(orders[r, t] for r in RETAILERS):>7}" for t in T)
          + f"{eu(sum(orders.values()), 0):>12}")
    print()
    print("Table 6 and §1.6. Setup cost (EUR/setup) and holding cost (EUR/(bike*week)): "
          + "City; Trekking; Mountain; Cargo")
    for f in F:
        print(f"{f}: setup cost {'; '.join(eu(v, 0) for v in setup_cost(SETUP[f]).values())}; "
              f"holding cost {'; '.join(eu(v) for v in holding_cost(f).values())}")

    title("§2 From the master plan to the weekly shipments of each plant")
    cost, v = solve_m4(orders)
    print(f"M4 with the orders of Table 4: cost {eu(cost)} EUR; backorders {eu(sum(v['b'].values()), 0)} and "
          f"lost sales {eu(sum(v['l'].values()), 0)} bikes")
    m = from_master_plan(v)
    print()
    print("Table 7. Plan of M4 at each plant and least stock at the end of each month (bikes)")
    print(f"{'Plant':<9}{'Month':<6}{'Assembled':>10}{'Shipped':>9}{'Stock':>7}   Least stock")
    for f in F:
        for t in T:
            print(f"{f:<9}{t:<6}{eu(v['p'][f, t], 0):>10}{eu(m['shipped'][f, t], 0):>9}{eu(v['h'][f, t], 0):>7}"
                  f"   {bikes(m['least'][f, t])}")
    print("Stock of the network at the end of each month (bikes): "
          + "; ".join(f"{t} {eu(m['network'][t], 0)}" for t in T))
    print()
    print("Table 8. Product mix of the shipments and split of the seasonal stock (%)")
    print(f"{'':<28}" + "".join(f"{t:>7}" for t in T))
    for label, key in (("Shipments", "mix"), ("Seasonal stock", "split")):
        for j in MODELS:
            print(f"{label + ', ' + j:<28}" + "".join(
                f"{eu(100 * m[key][t][j], 1) if key == 'mix' or m['network'][t] else '—':>7}" for t in T))
    print()
    print("Table 9. Shipments of each plant in each week (bikes): City; Trekking; Mountain; Cargo")
    for w in WEEKS:
        print(f"{w:<6}" + "".join(f"{bikes({j: m['x'][f, j, w] for j in MODELS}):>20}" for f in F))
    print(f"{'Total':<6}" + "".join(f"{bikes({j: sum(m['x'][f, j, w] for w in WEEKS) for j in MODELS}):>20}"
                                  for f in F))

    title("§3 Weekly lot plans of the three plants")
    plans = {}
    for k, f in enumerate(F):
        weeks, plan_cost, others = weekly_plan(f, m["x"], m["least"])
        plans[f] = weeks
        print(f"Table {10 + k}. Weekly lot plan of {f.lower()}: setup and holding cost {eu(plan_cost)} EUR; "
              f"another plan with the same costs in: {', '.join(others) if others else 'no month'}")
        print(f"{'Week':<6}{'Available':>10}{'Assembled':>20}{'Stock at the end':>18}{'Assembly':>10}"
              f"{'Setups':>8}{'Overload':>10}")
        for w, r in weeks.items():
            print(f"{w:<6}{eu(r['available'], 0):>10}{bikes(r['assembled']):>20}{bikes(r['stock']):>18}"
                  f"{eu(r['assembly']):>10}{eu(r['setup hours']):>8}{eu(r['overload']):>10}")
        print(f"{'Total':<6}{eu(sum(r['available'] for r in weeks.values()), 0):>10}"
              f"{bikes({j: sum(r['assembled'][j] for r in weeks.values()) for j in MODELS}):>20}{'':>18}"
              f"{eu(sum(r['assembly'] for r in weeks.values())):>10}"
              f"{eu(sum(r['setup hours'] for r in weeks.values())):>8}"
              f"{eu(sum(r['overload'] for r in weeks.values())):>10}")
        print()
    print("Step 7. The plan that assembles each week what it ships")
    for f in F[:2]:
        weeks, plan_cost, _ = weekly_plan(f, m["x"], m["least"], lot_for_lot=True)
        print(f"{f}: capacity overload {eu(sum(r['overload'] for r in weeks.values()))} h; setup and holding "
              f"cost {eu(plan_cost)} EUR. The plan of the model: "
              f"{eu(sum(r['overload'] for r in plans[f].values()))} h")
    for f, w in (("Plant 1", 13), ("Plant 2", 14)):
        r = plans[f][w]
        print(f"{f}, week {w}: capacity overload {eu(100 * r['overload'] / r['available'], 0)} % of the available "
              f"capacity; stock at the end of week {w - 1}: {sum(plans[f][w - 1]['stock'].values())} bikes, "
              f"its storage capacity {K_h[f]}")

    title("§4 Capacity overload and spare capacity at each plant")
    print("Table 13. Hours of the line of each plant, by month")
    print(f"{'Plant':<9}{'Month':<12}{'Available':>10}{'Assembly':>10}{'Setups':>8}{'Overload':>10}{'Spare':>9}"
          f"{'Overload %':>12}")
    for f in F:
        hours = {key: by_month(plans[f], key) for key in ("available", "assembly", "setup hours", "overload", "spare")}
        for t in [*T, "Six months"]:
            row = ({key: sum(hours[key].values()) for key in hours} if t == "Six months"
                   else {key: hours[key][t] for key in hours})
            print(f"{f:<9}{t:<12}{eu(row['available'], 0):>10}{eu(row['assembly']):>10}{eu(row['setup hours']):>8}"
                  f"{eu(row['overload']):>10}{eu(row['spare']):>9}"
                  f"{eu(100 * row['overload'] / row['available'], 1):>12}")

    title("§5 Assumptions of the master plan behind the capacity overload")
    x6, least6 = same_mix(m["x"], m["least"])
    runs = {"As planned": {}, "No holidays": {"k_w": "no holidays"}, "Half the setup times": {"a_set": "half"},
            "Setup times of plant 1": {"a_set": "plant 1"}, "Six-month product mix in every week": {"mix": True}}
    results = {}
    for f in F:
        for name, change in runs.items():
            if name == "Setup times of plant 1" and f == F[0]:
                continue
            k_w = available_capacity(f, {g: [] for g in F}) if change.get("k_w") else None
            a_set = ({j: SETUP[f][j] / 2 for j in MODELS} if change.get("a_set") == "half"
                     else SETUP[F[0]] if change.get("a_set") == "plant 1" else None)
            x, least = (x6, least6) if change.get("mix") else (m["x"], m["least"])
            weeks, _, others = weekly_plan(f, x, least, a_set=a_set, k_w=k_w)
            results[f, name] = (by_month(weeks, "overload"), by_month(weeks, "spare"), others)
    for k, (label, index) in enumerate((("Capacity overload", 0), ("Spare capacity", 1))):
        print(f"Table {14 + k}. {label} (h) of each plant, by month, in each run")
        print(f"{'':<48}" + "".join(f"{t:>9}" for t in T) + f"{'Six months':>12}")
        for (f, name), result in results.items():
            values = result[index]
            print(f"{f + ', ' + name:<48}" + "".join(f"{eu(values[t]):>9}" for t in T)
                  + f"{eu(sum(values.values())):>12}")
        print()
    print("Months in which another plan has the same costs:")
    for (f, name), result in results.items():
        if result[2]:
            print(f"{f}, {name}: {', '.join(result[2])}")
