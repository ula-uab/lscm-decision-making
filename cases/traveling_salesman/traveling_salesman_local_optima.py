# Traveling salesman - shortest route and local optima
#
# This script reproduces §6 of traveling_salesman.md (same folder): the
# shortest route, calculated by dynamic programming over subsets of cities, the
# routes with that length, how far each heuristic of §3-§5 is above it
# (Table 8), and where the local search with the reversal of a sub-path stops
# from routes drawn at random (Table 9).
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later. Nothing else has to be installed: the
# script only uses the standard library.
#
# How to run it (from this folder):
#     Windows:          python traveling_salesman_local_optima.py
#     macOS and Linux:  python3 traveling_salesman_local_optima.py
#
# The 20,000 searches from random routes take a few seconds.

import math
import random
from collections import Counter


# ---------------------------------------------------------------------------
# Random starting routes: how many, and the seed of the random numbers. With
# these two values the script prints Table 9 of the document; change them and
# run the script again.
# ---------------------------------------------------------------------------

STARTS = 20000
SEED = 1


# ---------------------------------------------------------------------------
# §1 Data (Tables 1 and 2): Ivanov et al. (2025), Table 14.3 and Fig. 14.4
# ---------------------------------------------------------------------------

# The cities, numbered as in the source: abbreviation and coordinates (x, y).
# The coordinates are used only for the angle of the sweep.
ABBR = {1: "HH", 2: "HB", 3: "H", 4: "BS", 5: "KI", 6: "HL", 7: "HR", 8: "OS", 9: "OL", 10: "WOB",
        11: "GÖ", 12: "BHV", 13: "HIL", 14: "SZG"}
XY = {1: (253, 372), 2: (151, 282), 3: (231, 155), 4: (302, 150), 5: (262, 515), 6: (311, 425),
      7: (427, 462), 8: (89, 140), 9: (99, 297), 10: (320, 170), 11: (249, 12), 12: (133, 365),
      13: (249, 117), 14: (279, 117)}
CITIES = list(ABBR)
HOME = 1   # Hamburg: the round trip starts and ends here

# Distance between each pair of cities (km), Table 2: one row per city i, one
# column per city j, in the order 1 to 14
ROWS = [
    [0, 136, 218, 227, 143, 79, 196, 284, 171, 213, 360, 120, 255, 256],
    [136, 0, 150, 201, 258, 215, 330, 155, 54, 203, 287, 85, 192, 209],
    [218, 150, 0, 71, 361, 282, 364, 143, 194, 90, 144, 232, 42, 61],
    [227, 201, 71, 0, 367, 275, 336, 213, 251, 27, 148, 273, 62, 40],
    [143, 258, 361, 367, 0, 102, 173, 413, 272, 350, 503, 198, 398, 398],
    [79, 215, 282, 275, 102, 0, 122, 361, 248, 255, 418, 188, 314, 310],
    [196, 330, 364, 336, 173, 122, 0, 467, 367, 311, 484, 310, 388, 375],
    [284, 155, 143, 213, 413, 361, 467, 0, 157, 233, 205, 229, 162, 191],
    [171, 54, 194, 251, 272, 248, 367, 157, 0, 255, 322, 76, 234, 255],
    [213, 203, 90, 27, 350, 255, 311, 233, 255, 0, 173, 270, 89, 67],
    [360, 287, 144, 148, 503, 418, 484, 205, 322, 173, 0, 372, 105, 109],
    [120, 85, 232, 273, 198, 188, 310, 229, 76, 270, 372, 0, 274, 288],
    [255, 192, 42, 62, 398, 314, 388, 162, 234, 89, 105, 274, 0, 30],
    [256, 209, 61, 40, 398, 310, 375, 191, 255, 67, 109, 288, 30, 0],
]
d = {i: {j: ROWS[i - 1][j - 1] for j in CITIES} for i in CITIES}
OTHERS = [i for i in CITIES if i != HOME]


def length(route):
    """Sum of the distances between consecutive cities (km)."""
    return sum(d[a][b] for a, b in zip(route, route[1:]))


def label(route):
    return ", ".join(ABBR[i] for i in route)


# ---------------------------------------------------------------------------
# §6 Shortest route: dynamic programming over subsets of cities
#
# best[S][j] is the length of the shortest path that leaves home, visits every
# city of the set S once and ends at j:
#     best[{j}][j] = d(home, j)
#     best[S][j]   = min over k in S - {j} of best[S - {j}][k] + d(k, j)
# The shortest route is min over j of best[all][j] + d(j, home). A set is a
# number whose bit a is 1 if the city OTHERS[a] is in it: 2^13 = 8,192 sets.
# ---------------------------------------------------------------------------

def shortest_routes():
    """The length of the shortest route and every route with that length (both directions)."""
    n = len(OTHERS)
    best = [dict() for _ in range(1 << n)]
    for a, j in enumerate(OTHERS):
        best[1 << a][a] = d[HOME][j]
    for subset in range(1, 1 << n):
        for a, value in best[subset].items():
            for b in range(n):
                if not subset >> b & 1:
                    new = value + d[OTHERS[a]][OTHERS[b]]
                    if new < best[subset | 1 << b].get(b, math.inf):
                        best[subset | 1 << b][b] = new
    full = (1 << n) - 1
    shortest = min(value + d[OTHERS[a]][HOME] for a, value in best[full].items())

    def paths(subset, a):
        """Every shortest path through ``subset`` that ends at OTHERS[a]."""
        if subset == 1 << a:
            return [[HOME, OTHERS[a]]]
        rest = subset & ~(1 << a)
        return [path + [OTHERS[a]] for b, value in best[rest].items()
                if value + d[OTHERS[b]][OTHERS[a]] == best[subset][a] for path in paths(rest, b)]

    routes = [path + [HOME] for a, value in best[full].items()
              if value + d[OTHERS[a]][HOME] == shortest for path in paths(full, a)]
    return shortest, sorted(routes)


# ---------------------------------------------------------------------------
# The heuristics of §3-§5, to compare them with the shortest route
# ---------------------------------------------------------------------------

def nearest_neighbor():
    """From home, each time to the nearest city not yet visited; at the end, home."""
    route, left = [HOME], list(OTHERS)
    while left:
        nearest = min(left, key=lambda j: d[route[-1]][j])
        route.append(nearest)
        left.remove(nearest)
    return route + [HOME]


def sweep():
    """The cities in increasing order of their angle seen from home, from north, counterclockwise."""
    def angle(i):
        return math.degrees(math.atan2(-(XY[i][0] - XY[HOME][0]), XY[i][1] - XY[HOME][1])) % 360
    return [HOME] + sorted(OTHERS, key=angle) + [HOME]


def ivanov_pass(route):
    """For k = 1, ..., 12, swap the cities at k and k + 1 if the route gets shorter."""
    route = list(route)
    for k in range(1, 13):
        swapped = route[:k] + [route[k + 1], route[k]] + route[k + 2:]
        if length(swapped) < length(route):
            route = swapped
    return route


def moves(move):
    """Pairs (i, j) of the first and last position reversed, in the order of evaluation."""
    if move == "swap":
        return [(k, k + 1) for k in range(1, 13)]
    return [(i, j) for i in range(1, 14) for j in range(i + 1, 14)]


def local_optimum(route, move="reversal"):
    """The route where the local search with best improvement stops. Reversing
    positions i to j changes only the arcs (i - 1, i) and (j, j + 1), so the
    change in length is computed from four distances."""
    route = list(route)
    while True:
        best = None
        for i, j in moves(move):
            a, b, c, e = route[i - 1], route[i], route[j], route[j + 1]
            delta = d[a][c] + d[b][e] - d[a][b] - d[c][e]
            if best is None or delta < best[2]:
                best = (i, j, delta)
        i, j, delta = best
        if delta >= 0:
            return route
        route = route[:i] + route[i:j + 1][::-1] + route[j + 1:]


def random_starts(starts, seed):
    """§6: the search with the reversal of a sub-path from ``starts`` random
    routes; for each length where it stops, how many starting routes."""
    random.seed(seed)
    stops = Counter()
    for _ in range(starts):
        order = list(range(2, 15))
        random.shuffle(order)
        stops[length(local_optimum([1] + order + [1]))] += 1
    return dict(sorted(stops.items()))


# ---------------------------------------------------------------------------
# Main: print the results in the order of the document
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


if __name__ == "__main__":

    title("§6 Shortest route")
    shortest, routes = shortest_routes()
    print(f"Dynamic programming over 2^{len(OTHERS)} = {2 ** len(OTHERS):,} sets of cities")
    print(f"Shortest route: {shortest:,} km")
    print(f"Routes with that length: {len(routes)} (each round trip in both directions)")
    for route in routes:
        print(f"  {label(route)}")

    print()
    print("Table 8. Each heuristic against the shortest route")
    nn, sw = nearest_neighbor(), sweep()
    rows = [("Nearest neighbor", nn), ("Sweep", sw),
            ("Pass of Ivanov et al. from the nearest neighbor", ivanov_pass(nn)),
            ("Swap of two adjacent cities from the nearest neighbor", local_optimum(nn, "swap")),
            ("Reversal of a sub-path from the nearest neighbor", local_optimum(nn)),
            ("Reversal of a sub-path from the sweep", local_optimum(sw))]
    print(f"{'Route':<56}{'km':>7}{'Above the shortest':>21}")
    for name, route in rows:
        print(f"{name:<56}{length(route):>7,}{100 * (length(route) - shortest) / shortest:>19.1f} %")

    title("§6 Local optima")
    stops = random_starts(STARTS, SEED)
    print(f"Table 9. Local search with the reversal of a sub-path from {STARTS:,} random routes (seed {SEED})")
    print(f"{'Length where it stops (km)':<28}{'Starting routes':>16}{'%':>8}")
    for km, count in stops.items():
        print(f"{km:<28,}{count:>16,}{100 * count / STARTS:>8.1f}")
    print(f"Different lengths where the search stops: {len(stops)}")
