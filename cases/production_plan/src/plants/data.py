"""Data of the example: Tables 1 and 2 of production_plan.md (M0), and the data
that each later version adds, with the stock at the plants of plant_stock.md (M1).
Each version keeps the data of the previous one and adds only its own.

The data are invented (2026); they do not describe a real company.
"""

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
d = FORECASTS["Forecast 1"]

# Reduced version (§3): plants 1 and 2, January, demand of January
REDUCED_F = ["Plant 1", "Plant 2"]
REDUCED_T = ["Jan"]

# ---------------------------------------------------------------------------
# M1 · Stock at the plants, Table 1 of plant_stock.md. Solved with forecast 2
# ---------------------------------------------------------------------------

# Holding cost c_h[f] (EUR/(bike·month)): different at each plant, so that where
# the stock is held has one answer
c_h = {"Plant 1": 5, "Plant 2": 6, "Plant 3": 7}

# Stock h_0[f] at the end of December (bikes)
h_0 = {"Plant 1": 20, "Plant 2": 10, "Plant 3": 0}

# Stock h_end[f] that each plant must hold at the end of the horizon (bikes): the
# plan leaves the plants as it found them
h_end = dict(h_0)
