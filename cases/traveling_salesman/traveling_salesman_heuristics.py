# Traveling salesman - construction heuristics and local search
#
# This script reproduces §3 to §5 of traveling_salesman.md (same folder): the
# route of the nearest neighbor (Table 3), the order and the route of the sweep
# (Table 4), the pass of Ivanov et al. (Table 5) and the local search from the
# nearest neighbor with each move (Table 7) and from the sweep with the
# reversal of a sub-path.
#
# Running it is optional: it is support material, not part of the assessment.
#
# Requirements: Python 3.10 or later. Nothing else has to be installed: the
# script only uses the standard library.
#
# How to run it (from this folder):
#     Windows:          python traveling_salesman_heuristics.py
#     macOS and Linux:  python3 traveling_salesman_heuristics.py

import math


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


# ---------------------------------------------------------------------------
# A route is a list of cities that starts and ends at home: positions 0 to 14.
# ---------------------------------------------------------------------------

def length(route):
    """Sum of the distances between consecutive cities (km)."""
    return sum(d[a][b] for a, b in zip(route, route[1:]))


def label(route):
    return ", ".join(ABBR[i] for i in route)


# ---------------------------------------------------------------------------
# §3 Nearest neighbor and §4 sweep
# ---------------------------------------------------------------------------

def nearest_neighbor():
    """From home, each time to the nearest city not yet visited; at the end, home."""
    route, left = [HOME], [i for i in CITIES if i != HOME]
    while left:
        nearest = min(left, key=lambda j: d[route[-1]][j])
        route.append(nearest)
        left.remove(nearest)
    return route + [HOME]


def angle(i):
    """Angle of the line from home to city i, from north (+y), counterclockwise (degrees)."""
    dx, dy = XY[i][0] - XY[HOME][0], XY[i][1] - XY[HOME][1]
    return math.degrees(math.atan2(-dx, dy)) % 360


def sweep():
    """The cities in increasing order of their angle seen from home."""
    return [HOME] + sorted((i for i in CITIES if i != HOME), key=angle) + [HOME]


# ---------------------------------------------------------------------------
# §5 Local search
#
# Both moves reverse the cities from position i to position j: the swap of two
# adjacent cities (j = i + 1, i = 1, ..., 12) and the reversal of a sub-path
# (1 <= i < j <= 13). Reversing i to j takes out the arcs (i - 1, i) and
# (j, j + 1) and puts in (i - 1, j) and (i, j + 1). At each step every move is
# evaluated and the one that leaves the shortest route is made, if it is
# strictly shorter (with a tie, the first in the order of evaluation); the
# search stops when no move shortens the route.
# ---------------------------------------------------------------------------

def moves(move):
    if move == "swap":
        return [(k, k + 1) for k in range(1, 13)]
    return [(i, j) for i in range(1, 14) for j in range(i + 1, 14)]


def reverse(route, i, j):
    return route[:i] + route[i:j + 1][::-1] + route[j + 1:]


def local_search(start, move):
    """The steps of the search: (cities reversed, arcs out, arcs in, route)."""
    route = list(start)
    steps = [((), (), (), route)]
    while True:
        best = min(moves(move), key=lambda m: length(reverse(route, *m)))
        if length(reverse(route, *best)) >= length(route):
            return steps
        i, j = best
        out = ((route[i - 1], route[i]), (route[j], route[j + 1]))
        new = ((route[i - 1], route[j]), (route[i], route[j + 1]))
        reversed_cities = tuple(route[i:j + 1])
        route = reverse(route, i, j)
        steps.append((reversed_cities, out, new, route))


def ivanov_pass(start):
    """For k = 1, ..., 12: the sub-path at positions k - 1 to k + 2, before and
    after swapping the cities at k and k + 1; the swap is kept if it is shorter.
    Returns the route and the rows (k, sub-path, before, after)."""
    route, rows = list(start), []
    for k in range(1, 13):
        sub_path = route[k - 1:k + 3]
        before = length(sub_path)
        after = length([sub_path[0], sub_path[2], sub_path[1], sub_path[3]])
        rows.append((k, sub_path, before, after))
        if after < before:
            route = reverse(route, k, k + 1)
    return route, rows


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------

def title(text):
    print()
    print(text)
    print("=" * len(text))


def arc(a_b):
    return f"{ABBR[a_b[0]]}–{ABBR[a_b[1]]}"


def print_search(start, move):
    steps = local_search(start, move)
    print(f"{'Step':<6}{'Sub-path reversed':<34}{'Arcs out':<18}{'Arcs in':<18}{'km':>7}")
    for k, (cities, out, new, route) in enumerate(steps):
        print(f"{k:<6}{label(cities) or '— (start)':<34}{'; '.join(map(arc, out)) or '—':<18}"
              f"{'; '.join(map(arc, new)) or '—':<18}{length(route):>7,}")
    end = steps[-1][3]
    best = min(moves(move), key=lambda m: length(reverse(end, *m)))
    whole = " (the whole route in the other direction)" if best == (1, 13) else ""
    print(f"Stops at {label(end)}, {length(end):,} km. "
          f"Best move from there: {length(reverse(end, *best)):,} km{whole}")


if __name__ == "__main__":

    # §3 Nearest neighbor
    title("§3 Nearest neighbor")
    nn = nearest_neighbor()
    print("Table 3. Route of the nearest neighbor")
    print(f"{'Leg':<5}{'From':<6}{'To':<6}{'km':>6}{'So far (km)':>13}")
    total = 0
    for k, (a, b) in enumerate(zip(nn, nn[1:]), start=1):
        total += d[a][b]
        print(f"{k:<5}{ABBR[a]:<6}{ABBR[b]:<6}{d[a][b]:>6}{total:>13,}")
    print(f"Nearest neighbor: {label(nn)}, {length(nn):,} km")

    # §4 Sweep
    title("§4 Sweep")
    sw = sweep()
    print("Table 4. Order of the sweep: angle seen from HH, from north, counterclockwise")
    print(f"{'Order':<7}{'City':<6}{'Angle (degrees)':>16}")
    for k, i in enumerate(sw[1:-1], start=1):
        print(f"{k:<7}{ABBR[i]:<6}{angle(i):>16.1f}")
    print(f"Sweep: {label(sw)}, {length(sw):,} km")

    # §5 The pass of Ivanov et al.
    title("§5 Local search")
    after_pass, rows = ivanov_pass(nn)
    print("Table 5. Pass of Ivanov et al. from the nearest neighbor (sub-path in km)")
    print(f"{'It.':<5}{'Sub-path':<22}{'Before':>8}{'After':>8}  Kept")
    for k, sub_path, before, after in rows:
        print(f"{k:<5}{label(sub_path):<22}{before:>8}{after:>8}  {'yes' if after < before else ''}")
    print(f"After the pass: {label(after_pass)}, {length(after_pass):,} km, "
          f"{length(nn) - length(after_pass)} km less than the nearest neighbor")

    print()
    print("Local search from the nearest neighbor, swap of two adjacent cities")
    print_search(nn, "swap")
    print()
    print("Table 7. Local search from the nearest neighbor, reversal of a sub-path")
    print_search(nn, "reversal")
    print()
    print("Local search from the sweep, reversal of a sub-path")
    print_search(sw, "reversal")
