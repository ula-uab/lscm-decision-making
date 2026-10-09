# Supplier selection - decision tree with a supplier that may stop delivering
#
# This script reproduces §8 of supplier_selection.md (same folder): the buyer's
# rule (Table 5) and buying everything from the distributor E, compared with a
# decision tree when the supplier that serves more than one component may stop
# delivering during the year. It prints the branches of the tree (Table 12),
# the planned cost, the expected cost and the worst case of each strategy
# (Table 13), the probability that E stops below which E alone has the lower
# expected cost, and the number of final branches of a tree with every
# selection that covers the six components.
#
# The three other scripts of this folder:
#   supplier_selection_rule.py          the decision matrix and the buyer's rule;
#   supplier_selection_local_search.py  local search and the 31 sets of suppliers;
#   supplier_selection_solver.py        the integer model, solved with a solver.
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later. Nothing else has to be installed: the
# script only uses the standard library.
#
# How to run it (from this folder):
#     Windows:          python supplier_selection_decision_tree.py
#     macOS and Linux:  python3 supplier_selection_decision_tree.py

import itertools


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



# ---------------------------------------------------------------------------
# §8 Data of the decision tree. Invented (2026)
# ---------------------------------------------------------------------------

# Probability that a supplier stops delivering during the year. Only the
# suppliers that serve more than one component in a strategy are uncertain;
# the others are treated as reliable.
STOP_PROBABILITY = {"E": 0.05, "C": 0.10}

# Cost of moving one component to another supplier at short notice (kEUR per
# component): lost assembly, urgent transport and qualification of the new
# supplier
MOVE_COST = 100


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
# §8 The decision tree
# ---------------------------------------------------------------------------

def served(contracted):
    """The components that each contracted supplier serves."""
    purchase = assign(contracted)
    return {s: [m for m in M if purchase[m] == s] for s in contracted}


def uncertain(contracted):
    """The suppliers of a selection that serve more than one component."""
    return [s for s, components in served(contracted).items() if len(components) > 1]


def branches(contracted):
    """The branches of a strategy: (suppliers that stop, components moved,
    probability, annual cost in kEUR/year). The uncertain suppliers stop or not
    independently of each other: k uncertain suppliers give 2^k branches."""
    components = served(contracted)
    risky = uncertain(contracted)
    for s in risky:
        if s not in STOP_PROBABILITY:
            raise ValueError(f"No probability of stopping for {s}, which serves more than one component.")
    rows = []
    for stops in itertools.product((False, True), repeat=len(risky)):
        stopped = tuple(s for s, stop in zip(risky, stops) if stop)
        p = 1.0
        for s, stop in zip(risky, stops):
            p *= STOP_PROBABILITY[s] if stop else 1 - STOP_PROBABILITY[s]
        moved = sum(len(components[s]) for s in stopped)
        rows.append((stopped, moved, p, cost(contracted) + MOVE_COST * moved))
    return rows


def expected_cost(rows):
    """The cost of each branch times its probability, added up (kEUR/year)."""
    return sum(p * value for _, _, p, value in rows)


def worst_case(rows):
    """The highest cost among the branches (kEUR/year)."""
    return max(value for _, _, _, value in rows)


def covering_selections():
    """The sets of acceptable suppliers that cover every component (Table 6)."""
    return [combo for n in range(1, len(ACCEPTABLE) + 1)
            for combo in itertools.combinations(ACCEPTABLE, n) if assign(combo) is not None]


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

    # §4 The two strategies of the tree
    title("§4 The buyer's rule and the distributor alone")

    print_buyer_rule()
    rule = tuple(sorted(set(buyer_rule().values())))
    print()
    print_purchase("Everything from the distributor E", ("E",))

    # §8 Decision tree
    title("§8 Decision tree with a supplier that may stop delivering")

    strategies = {"Everything from E": ("E",), "Buyer's rule": rule}
    print(f"Probability of stopping: {', '.join(f'{s} {p}' for s, p in STOP_PROBABILITY.items())}. "
          f"Cost of moving a component: {MOVE_COST} kEUR.")
    for name, contracted in strategies.items():
        s = uncertain(contracted)[0]
        print(f"{name}: uncertain supplier {s}, which serves {', '.join(served(contracted)[s])}")

    print()
    print("Table 12. Branches of the tree")
    print(f"{'Strategy':<20}{'Uncertain':>10}  {'Outcome':<30}{'Probability':>12}"
          f"{'Annual cost (kEUR/year)':>26}")
    for name, contracted in strategies.items():
        risky = ", ".join(uncertain(contracted))
        for stopped, moved, p, value in branches(contracted):
            outcome = (f"{', '.join(stopped)} stops: {moved} components moved" if stopped
                       else f"{risky} keeps delivering")
            print(f"{name:<20}{risky:>10}  {outcome:<30}{p:>12.2f}{value:>26.2f}")

    print()
    print("Table 13. Planned cost, expected cost and worst case (kEUR/year)")
    print(f"{'Strategy':<20}{'Planned cost':>14}{'Expected cost':>15}{'Worst case':>12}")
    summary = {}
    for name, contracted in strategies.items():
        rows = branches(contracted)
        summary[name] = (cost(contracted), expected_cost(rows), worst_case(rows))
        print(f"{name:<20}{summary[name][0]:>14.2f}{summary[name][1]:>15.2f}{summary[name][2]:>12.2f}")
    for name, (planned, expected, worst) in summary.items():
        terms = " + ".join(f"{p:.2f} x {value:.2f}" for _, _, p, value in branches(strategies[name]))
        print(f"  Expected cost, {name}: {terms} = {expected:.2f} kEUR/year")

    # Probability that E stops at which both strategies have the same expected cost:
    # cost of E + p x MOVE_COST x 6 = expected cost of the rule
    moved_e = len(served(("E",))["E"])
    expected_rule = summary["Buyer's rule"][1]
    threshold = (expected_rule - cost(("E",))) / (MOVE_COST * moved_e)
    print()
    print("Everything from E has the lower expected cost while the probability that E stops is below")
    print(f"  ({expected_rule:.2f} - {cost(('E',)):.2f}) / ({MOVE_COST} x {moved_e}) = {threshold:.4f}")

    # Size of a tree with one branch per selection that covers the six components,
    # in which any contracted supplier may stop: 2^k final branches for k suppliers
    covering = covering_selections()
    print()
    print(f"A tree with the {len(covering)} selections that cover the six components, "
          "in which any contracted supplier may stop:")
    total = 0
    for k in range(1, len(ACCEPTABLE) + 1):
        n = sum(1 for s in covering if len(s) == k)
        if n:
            total += n * 2 ** k
            print(f"  {k} supplier{'s' if k > 1 else ' '}: {n:>2} selections x 2^{k} = {n * 2 ** k:>3} final branches")
    print(f"  Final branches in all: {total}")
