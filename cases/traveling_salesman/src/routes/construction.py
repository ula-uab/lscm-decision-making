"""Routes, their length, and the two construction heuristics (§3 and §4).

A route is a list of city numbers that starts and ends at home (Hamburg, 1)
and visits each of the other 13 cities once: positions 0 to 14, with home at
positions 0 and 14.
"""

from __future__ import annotations

import math
import random

from .data import ABBR, CITIES, HOME, XY, d


def length(route: list[int]) -> int:
    """Length of a route: the sum of the distances between consecutive cities (km)."""
    return sum(d[a][b] for a, b in zip(route, route[1:]))


def legs(route: list[int]) -> list[tuple[int, int, int]]:
    """Each leg of a route: (from, to, distance in km)."""
    return [(a, b, d[a][b]) for a, b in zip(route, route[1:])]


def label(route: list[int]) -> str:
    """'HH, HL, KI, …, HH' for a route."""
    return ", ".join(ABBR[i] for i in route)


def nearest_neighbor(start: int = HOME) -> list[int]:
    """§3: from home, go each time to the nearest city not yet visited; at the
    end, go back home. Greedy: each step takes the shortest leg available, and
    the leg back home is not taken into account until the end."""
    route, left = [start], [i for i in CITIES if i != start]
    while left:
        nearest = min(left, key=lambda j: d[route[-1]][j])
        route.append(nearest)
        left.remove(nearest)
    return route + [start]


def angle(i: int, center: int = HOME) -> float:
    """§4: angle of the line from the center to city i, measured from north
    (+y) counterclockwise, from 0 to 360 degrees."""
    dx, dy = XY[i][0] - XY[center][0], XY[i][1] - XY[center][1]
    return math.degrees(math.atan2(-dx, dy)) % 360


def sweep(center: int = HOME) -> list[int]:
    """§4: visit the cities in increasing order of their angle seen from home.
    The order is fixed before the first leg; no distance is compared."""
    order = sorted((i for i in CITIES if i != center), key=lambda i: angle(i, center))
    return [center] + order + [center]


def random_route(seed: int | None = None, rng: random.Random | None = None) -> list[int]:
    """A route that visits the 13 cities in random order. With the same seed,
    the same route. ``rng`` draws several routes from one sequence of random
    numbers (§6): ``random.Random(1)`` gives the same sequence as
    ``random.seed(1)``."""
    rng = rng or random.Random(seed)
    order = [i for i in CITIES if i != HOME]
    rng.shuffle(order)
    return [HOME] + order + [HOME]
