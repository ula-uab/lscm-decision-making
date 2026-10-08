# Supplier selection - decision matrix and buyer's rule
#
# This script reproduces §3 and §4 of supplier_selection.md (same folder): the
# weighted decision matrix of the batteries, without and with the price
# (Table 4), the buyer's rule and its cost (Table 5), and the cost of buying
# everything from the distributor E.
#
# The two other scripts of this folder go on from here:
#   supplier_selection_local_search.py  local search and the 31 sets of suppliers;
#   supplier_selection_solver.py        the integer model, solved with a solver.
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later. Nothing else has to be installed: the
# script only uses the standard library.
#
# How to run it (from this folder):
#     Windows:          python supplier_selection_rule.py
#     macOS and Linux:  python3 supplier_selection_rule.py


# ---------------------------------------------------------------------------
# §1 Data (Tables 1-3). Invented (2026)
# ---------------------------------------------------------------------------

S = ["A", "B", "C", "D", "E", "F"]                                        # suppliers
M = ["frames", "motors", "batteries", "wheels", "brakes", "displays"]     # components

# Bicycles assembled per year: the volume of each component (units/year)
VOLUME = 5000

# Price of each component at each supplier (EUR/unit), Table 1. A supplier
# that does not offer a component has no entry.
PRICE = {
    "A": {"frames": 81, "motors": 123, "brakes": 42},
    "B": {"motors": 121, "batteries": 140, "displays": 52},
    "C": {"frames": 80, "batteries": 136, "wheels": 58},
    "D": {"wheels": 60, "brakes": 43, "displays": 49},
    "E": {"frames": 82, "motors": 122, "batteries": 148, "wheels": 61, "brakes": 43, "displays": 50},
    "F": {"batteries": 130},
}

# Annual cost c[s][m] of buying the whole volume of m from s (kEUR/year),
# Table 2: price x 5,000 units / 1,000
c = {s: {m: PRICE[s][m] * VOLUME / 1000 for m in PRICE[s]} for s in S}

# Fixed annual cost f[s] of a contracted supplier (kEUR/year)
f = {s: 50 for s in S}

# Criteria of the scorecard and their weights, Table 3
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

# A supplier is acceptable if its weighted score is at least 6 points.
# a[s][m] = 1 if s offers m and is acceptable.
MIN_SCORE = 6
a = {s: {m: int(m in PRICE[s] and q[s] >= MIN_SCORE) for m in M} for s in S}
ACCEPTABLE = [s for s in S if q[s] >= MIN_SCORE]

# §3 Weight of the price in the decision matrix of the batteries
PRICE_WEIGHT = 0.40


# ---------------------------------------------------------------------------
# §3 Weighted decision matrix for one component
# ---------------------------------------------------------------------------

def price_scores(component):
    """Price score of each supplier that offers the component (points, 0-10):
    10 x (highest price - price) / (highest price - lowest price)."""
    prices = {s: PRICE[s][component] for s in S if component in PRICE[s]}
    high, low = max(prices.values()), min(prices.values())
    return {s: 10 * (high - p) / (high - low) for s, p in prices.items()}


def score_with_price(component, price_weight):
    """Weighted score with the price as one more criterion: the other weights
    are multiplied by (1 - price_weight)."""
    ps = price_scores(component)
    return {s: (1 - price_weight) * q[s] + price_weight * ps[s] for s in ps}


# ---------------------------------------------------------------------------
# §4 The buyer's rule
# ---------------------------------------------------------------------------

def buyer_rule():
    """For each component, the cheapest acceptable supplier (alphabetical
    order if two cost the same)."""
    return {m: min((s for s in ACCEPTABLE if a[s][m]), key=lambda s: (c[s][m], s)) for m in M}


def assign(contracted):
    """Given the contracted suppliers, the supplier of each component: the
    cheapest contracted supplier with an acceptable offer. None if a component
    has no contracted supplier."""
    purchase = {}
    for m in M:
        offers = [s for s in contracted if a[s][m]]
        if not offers:
            return None
        purchase[m] = min(offers, key=lambda s: (c[s][m], s))
    return purchase


def cost(contracted):
    """Annual cost of a selection: fixed costs plus purchases (kEUR/year)."""
    purchase = assign(contracted)
    return sum(f[s] for s in contracted) + sum(c[s][m] for m, s in purchase.items())


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


def print_purchase(name, contracted):
    """The supplier and annual cost of each component, and the total."""
    purchase = assign(contracted)
    bought = sum(c[s][m] for m, s in purchase.items())
    fixed = sum(f[s] for s in contracted)
    print(name)
    print(f"{'Component':<12}{'Supplier':>10}{'Annual cost (kEUR/year)':>26}")
    for m in M:
        print(f"{m:<12}{purchase[m]:>10}{c[purchase[m]][m]:>26.2f}")
    print(f"Contracted: {', '.join(contracted)}")
    print(f"Purchases {bought:.2f} + fixed costs {fixed:.2f} = {bought + fixed:.2f} kEUR/year")


def print_buyer_rule():
    """§4 The buyer's rule and its cost (Table 5)."""
    rule = buyer_rule()
    print_purchase("Table 5. The buyer's rule: for each component, the cheapest acceptable supplier",
                   tuple(sorted(set(rule.values()))))


# ---------------------------------------------------------------------------
# Main: print the results in the order of the document
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # §3 Weighted decision matrix for the batteries
    title("§3 Weighted decision matrix for the batteries")

    print("Weighted score of each supplier (points, 0-10):")
    for s in S:
        status = "acceptable" if q[s] >= MIN_SCORE else "not acceptable"
        print(f"  {s}: {q[s]:.2f} ({status})")

    batteries = [s for s in S if "batteries" in PRICE[s]]
    ps = price_scores("batteries")
    with_price = score_with_price("batteries", PRICE_WEIGHT)
    weights = ", ".join(f"{k} {100 * (1 - PRICE_WEIGHT) * WEIGHTS[k]:.0f} %" for k in CRITERIA)
    print()
    print(f"Table 4. Batteries: weights with the price ({100 * PRICE_WEIGHT:.0f} %): {weights}")
    print(f"{'Supplier':<10}{'Price (EUR/unit)':>18}{'Price score':>13}"
          f"{'Score without price':>21}{'Score with price':>18}")
    for s in sorted(batteries, key=lambda s: -with_price[s]):
        print(f"{s:<10}{PRICE[s]['batteries']:>18}{ps[s]:>13.2f}{q[s]:>21.2f}{with_price[s]:>18.2f}")

    best = min((s for s in batteries if a[s]["batteries"]), key=lambda s: c[s]["batteries"])
    print()
    print(f"Batteries, decided in euros among the acceptable suppliers: "
          f"{best}, {c[best]['batteries']:.2f} kEUR/year")

    # §4 The buyer's rule and the distributor alone
    title("§4 The buyer's rule and the distributor alone")

    print_buyer_rule()
    rule = tuple(sorted(set(buyer_rule().values())))
    print()
    print_purchase("Everything from the distributor E", ("E",))
    print(f"Saving against the buyer's rule: {cost(rule) - cost(('E',)):.2f} kEUR/year")
