# Supplier selection - buyer's rule followed by a local search
#
# This script reproduces §4 to §6 of supplier_selection.md (same folder): the
# buyer's rule (Table 5), the 31 sets of contracted suppliers and the 21 that
# cover every component (Table 6), and the local search, step by step, from
# the selection of the rule (Table 8) and from a selection chosen below. It
# also lists which of the 21 selections are local optima.
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later. Nothing else has to be installed: the
# script only uses the standard library.
#
# How to run it (from this folder):
#     Windows:          python supplier_selection_local_search.py
#     macOS and Linux:  python3 supplier_selection_local_search.py

import itertools


# ---------------------------------------------------------------------------
# Selection from which the second local search starts. Change it and run the
# script again: any set of the acceptable suppliers A, B, C, D, E that covers
# every component.
# ---------------------------------------------------------------------------

START = ("E",)


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
# A selection is the set of contracted suppliers, written as a tuple in
# alphabetical order: ("C", "E"). Given the set, each component is bought from
# the cheapest contracted supplier with an acceptable offer for it.
# ---------------------------------------------------------------------------

def assign(contracted):
    """The supplier of each component, or None if a component has no
    contracted supplier (alphabetical order if two cost the same)."""
    purchase = {}
    for m in M:
        offers = [s for s in contracted if a[s][m]]
        if not offers:
            return None
        purchase[m] = min(offers, key=lambda s: (c[s][m], s))
    return purchase


def cost(contracted):
    """Annual cost of a selection: fixed costs plus purchases (kEUR/year).
    None if the selection leaves a component without a supplier."""
    purchase = assign(contracted)
    if purchase is None:
        return None
    return sum(f[s] for s in contracted) + sum(c[s][m] for m, s in purchase.items())


def uncovered(contracted):
    """Components that no contracted supplier offers."""
    return [m for m in M if not any(a[s][m] for s in contracted)]


def label(contracted):
    return ", ".join(contracted)


# ---------------------------------------------------------------------------
# §4 The buyer's rule
# ---------------------------------------------------------------------------

def buyer_rule():
    """For each component, the cheapest acceptable supplier (alphabetical
    order if two cost the same)."""
    return {m: min((s for s in ACCEPTABLE if a[s][m]), key=lambda s: (c[s][m], s)) for m in M}


# ---------------------------------------------------------------------------
# §5 Every set of suppliers
# ---------------------------------------------------------------------------

def all_selections():
    """Every non-empty set of acceptable suppliers: 2^5 - 1 = 31."""
    return [combo for n in range(1, len(ACCEPTABLE) + 1)
            for combo in itertools.combinations(ACCEPTABLE, n)]


def covering_selections():
    """The selections that cover every component, from the cheapest; with the
    same cost, from the smallest, then in alphabetical order."""
    covering = [s for s in all_selections() if cost(s) is not None]
    return sorted(covering, key=lambda s: (cost(s), len(s), s))


# ---------------------------------------------------------------------------
# §6 Local search
#
# A move removes a supplier, adds one, or swaps a contracted supplier for one
# that is not contracted. A move that leaves a component without a supplier is
# not allowed. At each step the search makes the move that lowers the cost
# most (if two give the same cost, the first in the order removals, additions,
# swaps), and it stops when no move lowers it.
# ---------------------------------------------------------------------------

def moves(contracted):
    """Every move from a selection, allowed or not: (description, new selection)."""
    outside = [s for s in ACCEPTABLE if s not in contracted]
    result = []
    for s in contracted:
        result.append((f"remove {s}", tuple(x for x in contracted if x != s)))
    for s in outside:
        result.append((f"add {s}", tuple(sorted(contracted + (s,)))))
    for out in contracted:
        for new in outside:
            result.append((f"swap {out} for {new}",
                           tuple(sorted(tuple(x for x in contracted if x != out) + (new,)))))
    return result


def neighbours(contracted):
    """The allowed moves."""
    return [(move, new) for move, new in moves(contracted) if new and cost(new) is not None]


def is_local_optimum(contracted):
    """True if no allowed move lowers the cost."""
    return all(cost(new) >= cost(contracted) for _, new in neighbours(contracted))


def local_search(start):
    """The steps of the search: (move, selection, cost), starting selection first."""
    current = tuple(sorted(start))
    steps = [("start", current, cost(current))]
    while True:
        options = neighbours(current)
        if not options:
            return steps
        move, new = min(options, key=lambda option: cost(option[1]))
        if cost(new) >= cost(current):
            return steps
        current = new
        steps.append((move, current, cost(current)))


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


def print_search(start):
    """The local search from a selection, step by step, and the neighbours of
    the selection where it stops."""
    steps = local_search(start)
    for i, (move, selection, value) in enumerate(steps):
        print(f"  Step {i}: {move:<14} -> {label(selection):<14} {value:.2f} kEUR/year")
    end = steps[-1][1]
    print(f"  Local optimum: {label(end)}. Its neighbours, from the cheapest:")
    for move, new in sorted(neighbours(end), key=lambda option: cost(option[1])):
        print(f"    {move:<14} -> {label(new):<14} {cost(new):.2f}")
    for move, new in moves(end):
        if not new or cost(new) is None:
            missing = uncovered(new) if new else M
            print(f"    {move:<14} not allowed: {', '.join(missing)} without a supplier")


# ---------------------------------------------------------------------------
# Main: print the results in the order of the document
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # §4 The buyer's rule
    title("§4 The buyer's rule")
    print_buyer_rule()
    rule = tuple(sorted(set(buyer_rule().values())))

    # §5 How many selections
    title("§5 Number of selections")
    selections = all_selections()
    covering = covering_selections()
    print(f"Sets of contracted suppliers: 2^{len(ACCEPTABLE)} - 1 = {len(selections)}")
    print(f"Sets that cover the six components: {len(covering)}")
    print(f"With 60 suppliers: 2^60 = {2 ** 60:.2e}")
    print()
    print("Table 6. The 21 selections that cover every component, from the cheapest")
    print(f"{'Rank':<6}{'Selection':<16}{'Purchases':>11}{'Fixed costs':>13}"
          f"{'Annual cost (kEUR/year)':>25}{'Local optimum':>15}")
    for rank, s in enumerate(covering, start=1):
        fixed = sum(f[x] for x in s)
        optimum = "yes" if is_local_optimum(s) else ""
        print(f"{rank:<6}{label(s):<16}{cost(s) - fixed:>11.2f}{fixed:>13.2f}"
              f"{cost(s):>25.2f}{optimum:>15}")
    print(f"Cheapest selection: {label(covering[0])}, {cost(covering[0]):.2f} kEUR/year")

    # §6 Local search
    title("§6 Local search")
    print(f"Table 8. Local search from the selection of the buyer's rule ({label(rule)})")
    print_search(rule)
    print()
    print(f"Local search from {label(tuple(sorted(START)))}")
    if uncovered(START):
        print(f"  Not valid: {', '.join(uncovered(START))} without a supplier.")
    else:
        print_search(START)
    print()
    optima = [s for s in covering if is_local_optimum(s)]
    print("Local optima among the 21 selections: "
          + "; ".join(f"{label(s)} ({cost(s):.2f})" for s in optima))
