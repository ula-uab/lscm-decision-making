"""Local search on a route: Ivanov's pass and the search with best improvement (§5).

A move changes a route into another one. Both moves of the case reverse the
cities of the route from position i to position j:

- **swap of two adjacent cities**: positions k and k + 1, with k = 1, ..., 12;
- **reversal of a sub-path**: positions i to j, with 1 <= i < j <= 13.

A swap of two adjacent cities is the reversal of a sub-path of two cities.
Reversing positions i to j takes out the arcs (i - 1, i) and (j, j + 1) and puts
in the arcs (i - 1, j) and (i, j + 1); every other arc stays, traveled in the
other direction inside the sub-path, which does not change its length because
the distances are symmetric. So the change in length of a move is computed
from four distances.
"""

from __future__ import annotations

import random
from collections import Counter

from .construction import label, length, random_route
from .data import ABBR, d

MOVES = {"swap": "swap of two adjacent cities", "reversal": "reversal of a sub-path"}


def moves(move: str, n: int = 15) -> list[tuple[int, int]]:
    """The neighborhood of a route of n positions, as pairs (i, j) of the first
    and last position reversed, in the order in which they are evaluated."""
    last = n - 2  # the last position that is not home
    if move == "swap":
        return [(k, k + 1) for k in range(1, last)]
    if move == "reversal":
        return [(i, j) for i in range(1, last + 1) for j in range(i + 1, last + 1)]
    raise ValueError(f"Unknown move {move!r}: the moves are {', '.join(MOVES)}.")


def apply(route: list[int], i: int, j: int) -> list[int]:
    """The route with positions i to j reversed."""
    return route[:i] + route[i:j + 1][::-1] + route[j + 1:]


def change(route: list[int], i: int, j: int) -> int:
    """Change in length of reversing positions i to j (km); negative if the route gets shorter."""
    a, b, c, e = route[i - 1], route[i], route[j], route[j + 1]
    return d[a][c] + d[b][e] - d[a][b] - d[c][e]


def arcs(route: list[int], i: int, j: int) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """The two arcs that reversing positions i to j takes out, and the two it puts in."""
    a, b, c, e = route[i - 1], route[i], route[j], route[j + 1]
    return [(a, b), (c, e)], [(a, c), (b, e)]


def arc_label(arc: tuple[int, int]) -> str:
    """'HL–KI' for the arc (6, 5)."""
    return f"{ABBR[arc[0]]}–{ABBR[arc[1]]}"


def best_move(route: list[int], move: str) -> tuple[int, int, int]:
    """The move of the neighborhood that leaves the shortest route: (i, j, change).
    With a tie, the first one in the order of evaluation."""
    best = None
    for i, j in moves(move, len(route)):
        delta = change(route, i, j)
        if best is None or delta < best[2]:
            best = (i, j, delta)
    return best


def is_local_optimum(route: list[int], move: str) -> bool:
    """True if no move of the neighborhood shortens the route."""
    return best_move(route, move)[2] >= 0


def search(start: list[int], move: str) -> list[dict]:
    """§5: local search with best improvement. At each step every move of the
    neighborhood is evaluated and the one that leaves the shortest route is
    made, if it is strictly shorter than the current route. The search stops at
    a local optimum: no move shortens the route.

    Returns the starting route (step 0) and one row per move made, with the
    cities reversed (in their order before the move), the arcs out and in, the
    length and the route."""
    route = list(start)
    steps = [{"step": 0, "reversed": [], "out": [], "in": [], "length": length(route), "route": route}]
    while True:
        i, j, delta = best_move(route, move)
        if delta >= 0:
            return steps
        out, new = arcs(route, i, j)
        reversed_cities = route[i:j + 1]
        route = apply(route, i, j)
        steps.append({"step": len(steps), "reversed": reversed_cities, "out": out, "in": new,
                      "length": length(route), "route": route})


def local_optimum(start: list[int], move: str) -> list[int]:
    """The route where the search from ``start`` stops, without keeping the steps."""
    route = list(start)
    while True:
        i, j, delta = best_move(route, move)
        if delta >= 0:
            return route
        route = apply(route, i, j)


def random_starts(starts: int, seed: int = 1, move: str = "reversal") -> dict[int, int]:
    """§6: the search from ``starts`` routes drawn at random, one after another
    from the same sequence of random numbers (``random.seed(seed)`` once). For
    each length where the search stops, the number of starting routes, from the
    shortest length."""
    rng = random.Random(seed)
    stops = Counter(length(local_optimum(random_route(rng=rng), move)) for _ in range(starts))
    return dict(sorted(stops.items()))


def ivanov_pass(start: list[int]) -> tuple[list[int], list[dict]]:
    """§5: the pass of Ivanov et al. (2025, §14.3.3, iterations 1 to 12). For
    k = 1, ..., 12, compare the sub-path of four cities at positions k - 1 to
    k + 2 with the same sub-path with the cities at k and k + 1 swapped, and keep
    the swap if it is shorter. The pass goes on from the route already changed.

    Returns the route at the end of the pass and one row per iteration."""
    route, rows = list(start), []
    for k in range(1, len(route) - 2):
        sub_path = route[k - 1:k + 3]
        swapped = [sub_path[0], sub_path[2], sub_path[1], sub_path[3]]
        before, after = length(sub_path), length(swapped)
        rows.append({"iteration": k, "sub_path": sub_path, "before": before, "after": after,
                     "confirmed": after < before})
        if after < before:
            route = apply(route, k, k + 1)
    return route, rows


def describe(step: dict) -> str:
    """One line for a step of the search."""
    if not step["step"]:
        return f"Step 0: start, {step['length']:,} km"
    return (f"Step {step['step']}: reverse {label(step['reversed'])}; out "
            f"{', '.join(map(arc_label, step['out']))}; in {', '.join(map(arc_label, step['in']))}; "
            f"{step['length']:,} km")
