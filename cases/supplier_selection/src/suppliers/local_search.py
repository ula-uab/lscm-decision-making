"""Local search on the set of contracted suppliers (§6).

A solution is the set of contracted suppliers; given the set, each component is
bought from the cheapest contracted supplier (``selection.assign``). A move
removes a supplier, adds one, or swaps a contracted supplier for one that is not
contracted. A move that leaves a component without a supplier is not allowed.
At each step the search makes the move that lowers the cost most, and it stops
when no move lowers it: the selection is then a local optimum.

If two moves give the same cost, the first one in this order is made: removals,
additions, swaps, each in alphabetical order.
"""

from __future__ import annotations

from .data import M
from .selection import ACCEPTABLE, cost, label, selection, uncovered


def _moves(contracted, suppliers=ACCEPTABLE) -> list[tuple[str, tuple]]:
    """Every move from a selection, allowed or not: (description, new selection)."""
    contracted = selection(contracted)
    outside = [s for s in suppliers if s not in contracted]
    moves = []
    for s in contracted:
        moves.append((f"remove {s}", selection(set(contracted) - {s})))
    for s in outside:
        moves.append((f"add {s}", selection(set(contracted) | {s})))
    for out in contracted:
        for new in outside:
            moves.append((f"swap {out} for {new}", selection(set(contracted) - {out} | {new})))
    return moves


def neighbours(contracted, suppliers=ACCEPTABLE) -> list[tuple[str, tuple]]:
    """Every allowed move from a selection: (description, new selection)."""
    return [(move, new) for move, new in _moves(contracted, suppliers) if new and cost(new) is not None]


def blocked(contracted, suppliers=ACCEPTABLE) -> list[tuple[str, list[str]]]:
    """The moves that are not allowed, with the components they leave without a supplier."""
    return [(move, uncovered(new) if new else list(M)) for move, new in _moves(contracted, suppliers)
            if not new or cost(new) is None]


def best_move(contracted, suppliers=ACCEPTABLE) -> tuple[str, tuple, float] | None:
    """The allowed move with the lowest cost, or None if there is no allowed move."""
    options = neighbours(contracted, suppliers)
    if not options:
        return None
    move, new = min(options, key=lambda option: cost(option[1]))
    return move, new, cost(new)


def is_local_optimum(contracted, suppliers=ACCEPTABLE) -> bool:
    """True if no allowed move lowers the cost of the selection."""
    best = best_move(contracted, suppliers)
    return best is None or best[2] >= cost(selection(contracted))


def search(start, suppliers=ACCEPTABLE) -> list[dict]:
    """The steps of the local search from a selection: the starting selection,
    then one row per move made. The last row is a local optimum."""
    current = selection(start)
    if cost(current) is None:
        raise ValueError(f"The selection {label(current)} leaves a component without a supplier.")
    steps = [{"step": 0, "move": "start", "selection": current, "cost": cost(current)}]
    while True:
        best = best_move(current, suppliers)
        if best is None or best[2] >= cost(current):
            return steps
        move, current, value = best
        steps.append({"step": len(steps), "move": move, "selection": current, "cost": value})


def local_optima(selections, suppliers=ACCEPTABLE) -> list[tuple]:
    """The selections of a list that are local optima."""
    return [s for s in selections if is_local_optimum(s, suppliers)]
