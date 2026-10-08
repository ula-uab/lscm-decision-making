"""Selections of suppliers and their annual cost, without a solver (§4-§6).

A selection is the set of contracted suppliers, written as a tuple in
alphabetical order: ("C", "E"). Given the set, each component is bought from
the cheapest contracted supplier with an acceptable offer for it. Its cost is
the fixed cost of the contracted suppliers plus the cost of the purchases.
"""

from __future__ import annotations

import itertools

from .data import MIN_SCORE, M, S, a, c, f, q

# The acceptable suppliers: weighted score of at least 6 points (A to E)
ACCEPTABLE = [s for s in S if q[s] >= MIN_SCORE]


def selection(suppliers) -> tuple:
    """A set of suppliers written as a tuple in alphabetical order."""
    chosen = tuple(sorted(set(suppliers)))
    wrong = [s for s in chosen if s not in S]
    if wrong:
        raise ValueError(f"Unknown supplier: {', '.join(wrong)}. The suppliers are {', '.join(S)}.")
    return chosen


def label(contracted) -> str:
    """'C, E' for the selection ('C', 'E')."""
    return ", ".join(contracted) if contracted else "none"


def assign(contracted, components=M) -> dict | None:
    """The supplier of each component: the cheapest contracted supplier with an
    acceptable offer (alphabetical order if two cost the same). None if some
    component has no contracted supplier that offers it."""
    purchase = {}
    for m in components:
        offers = [s for s in contracted if a[s][m]]
        if not offers:
            return None
        purchase[m] = min(offers, key=lambda s: (c[s][m], s))
    return purchase


def uncovered(contracted, components=M) -> list[str]:
    """The components that no contracted supplier offers with an acceptable offer."""
    return [m for m in components if not any(a[s][m] for s in contracted)]


def purchase_cost(purchase: dict) -> float:
    """Annual cost of the purchases (kEUR/year)."""
    return sum(c[s][m] for m, s in purchase.items())


def fixed_cost(contracted) -> float:
    """Annual fixed cost of the contracted suppliers (kEUR/year)."""
    return sum(f[s] for s in contracted)


def cost(contracted, components=M) -> float | None:
    """Annual cost of a selection: fixed costs plus purchases (kEUR/year).
    None if the selection leaves a component without a supplier."""
    purchase = assign(contracted, components)
    if purchase is None:
        return None
    return fixed_cost(contracted) + purchase_cost(purchase)


def buyer_rule(components=M, suppliers=ACCEPTABLE) -> dict:
    """The rule a buyer would apply: for each component, the cheapest acceptable
    supplier, as if no other component existed."""
    return {m: min((s for s in suppliers if a[s][m]), key=lambda s: (c[s][m], s))
            for m in components}


def contracted_by(purchase: dict) -> tuple:
    """The suppliers that a purchase plan contracts."""
    return selection(purchase.values())


def all_selections(suppliers=ACCEPTABLE) -> list[tuple]:
    """Every non-empty set of suppliers: 2^5 - 1 = 31 with the five acceptable ones."""
    return [combo for n in range(1, len(suppliers) + 1)
            for combo in itertools.combinations(sorted(suppliers), n)]


def covering_selections(suppliers=ACCEPTABLE, components=M) -> list[tuple]:
    """The selections that cover every component, from the cheapest; selections
    with the same cost go from the smallest, then in alphabetical order."""
    covering = [s for s in all_selections(suppliers) if assign(s, components) is not None]
    return sorted(covering, key=lambda s: (cost(s, components), len(s), s))
