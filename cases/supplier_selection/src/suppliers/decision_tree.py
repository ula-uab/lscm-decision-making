"""Decision tree with a supplier that may stop delivering (§8).

A strategy is a selection of suppliers. In a strategy, a supplier that serves
more than one component is uncertain: it may stop delivering during the year;
a supplier that serves one component is treated as reliable. When a supplier
stops, each of its components is moved to another supplier at short notice,
at a cost of MOVE_COST per component. The cost of a year is the planned cost
of the strategy plus that cost. The uncertain suppliers of a strategy stop or
not independently of each other, so k uncertain suppliers give 2^k branches.
"""

from __future__ import annotations

import itertools

from . import selection as sel
from .data import MOVE_COST, STOP_PROBABILITY


def strategies() -> dict:
    """The two strategies of the tree: everything from E and the buyer's rule."""
    return {"Everything from E": ("E",), "Buyer's rule": sel.contracted_by(sel.buyer_rule())}


def served(contracted) -> dict:
    """The components that each contracted supplier serves."""
    purchase = sel.assign(contracted)
    if purchase is None:
        raise ValueError(f"The selection {sel.label(contracted)} leaves "
                         f"{', '.join(sel.uncovered(contracted))} without a supplier.")
    return {s: [m for m, t in purchase.items() if t == s] for s in contracted}


def uncertain(contracted) -> list[str]:
    """The suppliers of a selection that serve more than one component."""
    return [s for s, components in served(contracted).items() if len(components) > 1]


def branches(contracted, probability: dict = STOP_PROBABILITY, move_cost: float = MOVE_COST) -> list[dict]:
    """The branches of a strategy: which uncertain suppliers stop, the components
    moved, the probability and the annual cost (kEUR/year). The first branch is
    the one in which no supplier stops."""
    components = served(contracted)
    risky = uncertain(contracted)
    missing = [s for s in risky if s not in probability]
    if missing:
        raise ValueError(f"No probability of stopping for {', '.join(missing)}: in the selection "
                         f"{sel.label(contracted)}, {', '.join(missing)} serves more than one component, "
                         "so it is uncertain and needs one.")
    planned = sel.cost(contracted)
    rows = []
    for stops in itertools.product((False, True), repeat=len(risky)):
        stopped = tuple(s for s, stop in zip(risky, stops) if stop)
        p = 1.0
        for s, stop in zip(risky, stops):
            p *= probability[s] if stop else 1 - probability[s]
        moved = sum(len(components[s]) for s in stopped)
        rows.append({"stopped": stopped, "moved": moved, "probability": p,
                     "cost": planned + move_cost * moved})
    return rows


def expected_cost(rows: list[dict]) -> float:
    """Expected cost: the cost of each branch times its probability, added up (kEUR/year)."""
    return sum(r["probability"] * r["cost"] for r in rows)


def worst_case(rows: list[dict]) -> float:
    """The highest cost among the branches (kEUR/year)."""
    return max(r["cost"] for r in rows)


def summary(contracted, probability: dict = STOP_PROBABILITY, move_cost: float = MOVE_COST) -> dict:
    """Planned cost, expected cost and worst case of a strategy (kEUR/year)."""
    rows = branches(contracted, probability, move_cost)
    return {"planned": sel.cost(contracted), "expected": expected_cost(rows), "worst": worst_case(rows)}


def threshold(against=None, probability: dict = STOP_PROBABILITY,
              move_cost: float = MOVE_COST) -> float | None:
    """The probability that E stops at which buying everything from E has the same
    expected cost as the strategy against (by default, the buyer's rule):
    cost of E + p x move_cost x 6 = expected cost of against. Below it, E alone has
    the lower expected cost. None if moving a component costs nothing."""
    against = strategies()["Buyer's rule"] if against is None else against
    only_e = ("E",)
    moved = len(served(only_e)["E"])
    if move_cost == 0:
        return None
    return (summary(against, probability, move_cost)["expected"] - sel.cost(only_e)) / (move_cost * moved)


def leaves(selections) -> int:
    """Final branches of a tree with one branch per selection, in which any
    contracted supplier may stop: 2^k for a selection of k suppliers."""
    return sum(2 ** len(s) for s in selections)
