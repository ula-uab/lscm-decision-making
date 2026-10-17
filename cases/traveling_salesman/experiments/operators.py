"""Genetic operators on the path representation of a route.

A route is a list of the n cities in the order of visit (Larrañaga et al.,
1999, §4.3); the salesman goes back from the last city to the first. Every
operator here returns routes as lists of the n cities; the caller turns them so
that home comes first (``rotate``), which does not change the route.

Sources:

- OX1: order crossover, Larrañaga et al. (1999, §4.3.3). Taken from DEAP
  (``deap.tools.cxOrdered``), checked against the example of the paper.
- ER: genetic edge recombination crossover, Larrañaga et al. (1999, §4.3.7),
  written here from the five steps of the paper.
- IVM: inversion mutation, Larrañaga et al. (1999, §4.3.16), written here.
- One-point crossover for sequences and exchange mutation: Klein and Faust
  (2015, §31.4), written here.
- Tournament selection: Klein and Faust (2015, §31.3), written here.

All random choices use the module ``random`` (DEAP uses it too), so a run is
reproducible with ``random.seed``.
"""

from __future__ import annotations

import random

from deap import tools


def rotate(route: list[int], home: int = 0) -> list[int]:
    """The same route, starting at home."""
    k = route.index(home)
    return route[k:] + route[:k]


# --- Crossovers --------------------------------------------------------------

def one_point(x: list[int], y: list[int], h: int | None = None) -> tuple[list[int], list[int]]:
    """Klein and Faust (2015, §31.4, Fig. 31.3): a crossover point h in [1, n - 1]
    is drawn; child A takes the first h positions of X and is filled up with the
    other elements in the order in which they are in Y; child B the other way round."""
    n = len(x)
    if h is None:
        h = random.randint(1, n - 1)
    head_x, head_y = x[:h], y[:h]
    in_x, in_y = set(head_x), set(head_y)
    return head_x + [c for c in y if c not in in_x], head_y + [c for c in x if c not in in_y]


def ox1(x: list[int], y: list[int]) -> tuple[list[int], list[int]]:
    """Larrañaga et al. (1999, §4.3.3), with ``deap.tools.cxOrdered``: two cut
    points are drawn; each child keeps the cities of one parent between the cut
    points and gets the other cities in the order in which they appear in the
    other parent, starting from the second cut point.

    DEAP works on the numbers 0, ..., n - 1 and changes its arguments, so it
    receives copies. The first child it returns keeps the segment of y."""
    c1, c2 = tools.cxOrdered(list(x), list(y))
    return list(c1), list(c2)


def edge_map(x: list[int], y: list[int]) -> dict[int, set[int]]:
    """Larrañaga et al. (1999, §4.3.7, Table 3): for each city, the cities joined
    to it by an edge in either parent (the routes are closed)."""
    edges = {c: set() for c in x}
    for route in (x, y):
        n = len(route)
        for k, c in enumerate(route):
            edges[c].update((route[k - 1], route[(k + 1) % n]))
    return edges


def er(x: list[int], y: list[int], rng=random) -> list[int]:
    """Larrañaga et al. (1999, §4.3.7), one child:

    1. choose the initial city from the initial cities of the two parents (the
       one with fewer entries in its edge list; ties at random); it is the
       current city;
    2. remove the current city from the edge lists of all cities;
    3. if the current city has entries in its edge list go to 4, else to 5;
    4. the city of the edge list of the current city with the fewest entries in
       its own edge list becomes the current city (ties at random); go to 2;
    5. if no city is left, stop; otherwise choose an unvisited city at random
       and go to 2.

    ``rng`` only needs a method ``choice``; the tests pass one that makes the
    choices of the example of the paper."""
    edges = edge_map(x, y)
    starts = sorted({x[0], y[0]})
    fewest = min(len(edges[c]) for c in starts)
    current = rng.choice([c for c in starts if len(edges[c]) == fewest])
    child, unvisited = [], set(x)
    while True:
        child.append(current)
        unvisited.discard(current)
        for c in edges[current]:
            edges[c].discard(current)
        if not unvisited:
            return child
        candidates = sorted(edges[current])
        if candidates:
            fewest = min(len(edges[c]) for c in candidates)
            current = rng.choice([c for c in candidates if len(edges[c]) == fewest])
        else:
            current = rng.choice(sorted(unvisited))


def er_pair(x: list[int], y: list[int]) -> tuple[list[int], list[int]]:
    """Two children of ER, each built on its own: ER gives one child per pair of
    parents, and the genetic algorithm replaces each pair by two children."""
    return er(x, y), er(x, y)


# --- Mutations ---------------------------------------------------------------

def exchange(route: list[int], i: int | None = None, j: int | None = None) -> list[int]:
    """Exchange mutation: two positions drawn at random swap their cities
    (Klein and Faust, 2015, §31.4; Larrañaga et al., 1999, §4.3.13, EM)."""
    if i is None:
        i, j = random.sample(range(len(route)), 2)
    out = list(route)
    out[i], out[j] = out[j], out[i]
    return out


def ivm(route: list[int], start: int | None = None, end: int | None = None,
        at: int | None = None) -> list[int]:
    """Inversion mutation (Larrañaga et al., 1999, §4.3.16): a sub-tour drawn at
    random (positions start to end) is removed from the route and inserted, in
    reversed order, at a position drawn at random among the cities left: ``at``
    is the number of cities left before it."""
    n = len(route)
    if start is None:
        start, end = sorted(random.sample(range(n), 2))
    sub = route[start:end + 1]
    rest = route[:start] + route[end + 1:]
    if at is None:
        at = random.randint(0, len(rest))
    return rest[:at] + sub[::-1] + rest[at:]


# --- Selection ---------------------------------------------------------------

def tournament(lengths: list[int], size: int, group: int = 2) -> list[int]:
    """Klein and Faust (2015, §31.3): the indices of the individuals are put in
    a random order and taken in successive groups of ``group``; the shortest
    route of each group (the first one if they tie) goes to the gene pool. When
    the list is used up, a new random order is drawn, until the pool has
    ``size`` individuals. Returns the indices of the pool."""
    pool: list[int] = []
    while True:
        order = list(range(len(lengths)))
        random.shuffle(order)
        for k in range(0, len(order) - group + 1, group):
            pool.append(min(order[k:k + group], key=lambda i: lengths[i]))
            if len(pool) == size:
                return pool
