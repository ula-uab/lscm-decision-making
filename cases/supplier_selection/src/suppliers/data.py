"""Data of the example, Tables 1-3 and §8 of supplier_selection.md.

The data are invented (2026); they do not describe a real company.
"""

S = ["A", "B", "C", "D", "E", "F"]                                        # suppliers
M = ["frames", "motors", "batteries", "wheels", "brakes", "displays"]     # components

# Bicycles assembled per year: the volume of each component (units/year)
VOLUME = 5000

# Price of each component at each supplier (EUR/unit), Table 1. A supplier that
# does not offer a component has no entry.
PRICE = {
    "A": {"frames": 81, "motors": 123, "brakes": 42},
    "B": {"motors": 121, "batteries": 140, "displays": 52},
    "C": {"frames": 80, "batteries": 136, "wheels": 58},
    "D": {"wheels": 60, "brakes": 43, "displays": 49},
    "E": {"frames": 82, "motors": 122, "batteries": 148, "wheels": 61, "brakes": 43, "displays": 50},
    "F": {"batteries": 130},
}

# Annual cost c[s][m] of buying the whole volume of m from s (kEUR/year),
# Table 2:
# price x 5,000 units / 1,000
c = {s: {m: PRICE[s][m] * VOLUME / 1000 for m in PRICE[s]} for s in S}

# Fixed annual cost f[s] of a contracted supplier (kEUR/year): qualification,
# audits, quality engineering and contract management
f = {s: 50 for s in S}

# Criteria of the supplier scorecard and their weights, Table 3
CRITERIA = ["Quality", "Delivery reliability", "Sustainability", "Financial strength"]
WEIGHTS = {"Quality": 0.35, "Delivery reliability": 0.25, "Sustainability": 0.20,
           "Financial strength": 0.20}

# Score of each supplier on each criterion (points, 0-10), Table 3
SCORES = {
    "A": {"Quality": 8, "Delivery reliability": 7, "Sustainability": 6, "Financial strength": 7},
    "B": {"Quality": 7, "Delivery reliability": 8, "Sustainability": 7, "Financial strength": 6},
    "C": {"Quality": 9, "Delivery reliability": 8, "Sustainability": 6, "Financial strength": 8},
    "D": {"Quality": 6, "Delivery reliability": 7, "Sustainability": 8, "Financial strength": 7},
    "E": {"Quality": 7, "Delivery reliability": 9, "Sustainability": 6, "Financial strength": 8},
    "F": {"Quality": 4, "Delivery reliability": 6, "Sustainability": 3, "Financial strength": 5},
}

# Weighted score q[s] (points, 0-10)
q = {s: sum(WEIGHTS[k] * SCORES[s][k] for k in CRITERIA) for s in S}

# A supplier is acceptable if its weighted score is at least 6 points
MIN_SCORE = 6

# a[s][m] = 1 if s offers m and is acceptable
a = {s: {m: int(m in PRICE[s] and q[s] >= MIN_SCORE) for m in M} for s in S}

# Weight of the price in the decision matrix of the batteries (§3)
PRICE_WEIGHT = 0.40

# Decision tree (§8, Table 12): probability that a supplier stops delivering
# during the year. Only the suppliers that serve more than one component in a
# strategy are uncertain; the others are treated as reliable.
STOP_PROBABILITY = {"E": 0.05, "C": 0.10}

# Cost of moving one component to another supplier at short notice when its
# supplier stops (kEUR per component): lost assembly, urgent transport and
# qualification of the new supplier (§8, Table 12)
MOVE_COST = 100

# Reduced version (§7): three suppliers, three components, the same costs
REDUCED_S = ["A", "B", "C"]
REDUCED_M = ["frames", "motors", "batteries"]
