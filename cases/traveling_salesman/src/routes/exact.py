"""The shortest route, by dynamic programming over subsets of cities (§6).

For each set S of cities other than home and each city j in S, ``best[S][j]`` is
the length of the shortest path that leaves home, visits every city of S once
and ends at j. It is built from the sets with one city up to the set of all 13:

    best[{j}][j] = d(home, j)
    best[S][j]   = min over k in S - {j} of  best[S - {j}][k] + d(k, j)

and the shortest route has length min over j of best[all][j] + d(j, home). With
13 cities there are 2^13 = 8,192 sets, and the calculation takes less than a second
without a solver. Every path that reaches the minimum is kept, so that all the
shortest routes are found, not only one.
"""

from __future__ import annotations

from .construction import label, length
from .data import ABBR, CITIES, HOME, d


def _table(home: int = HOME):
    """best[S][j] for every set S (a bit mask over ``others``) and every city j of S."""
    others = [i for i in CITIES if i != home]
    n = len(others)
    best = [dict() for _ in range(1 << n)]
    for a, j in enumerate(others):
        best[1 << a][a] = d[home][j]
    for subset in range(1, 1 << n):
        for a, value in best[subset].items():
            for b in range(n):
                if subset >> b & 1:
                    continue
                bigger, new = subset | 1 << b, value + d[others[a]][others[b]]
                if new < best[bigger].get(b, float("inf")):
                    best[bigger][b] = new
    return others, best


def shortest_routes(home: int = HOME) -> tuple[int, list[list[int]]]:
    """The length of the shortest route and every route with that length, in
    both directions."""
    others, best = _table(home)
    full = (1 << len(others)) - 1
    shortest = min(value + d[others[a]][home] for a, value in best[full].items())

    def paths(subset, a):
        """Every shortest path that visits ``subset`` and ends at others[a]."""
        if subset == 1 << a:
            return [[home, others[a]]]
        rest = subset & ~(1 << a)
        return [path + [others[a]] for b, value in best[rest].items()
                if value + d[others[b]][others[a]] == best[subset][a] for path in paths(rest, b)]

    routes = [path + [home] for a, value in best[full].items()
              if value + d[others[a]][home] == shortest for path in paths(full, a)]
    return shortest, sorted(routes)


def distinct(routes: list[list[int]]) -> list[list[int]]:
    """The routes that are different round trips: a route and the same route in
    the other direction count once. Each one is written in the direction whose
    second city comes first in alphabetical order of the abbreviations, and
    they are listed in that order."""
    kept = {}
    for route in routes:
        forward, backward = route, route[::-1]
        first = min(forward, backward, key=lambda r: ABBR[r[1]])
        kept[label(first)] = first
    return [kept[k] for k in sorted(kept, key=lambda k: ABBR[kept[k][1]])]


def gap(route: list[int], shortest: int) -> float:
    """How far a route is above the shortest one (%)."""
    return 100 * (length(route) - shortest) / shortest
