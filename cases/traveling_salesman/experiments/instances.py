"""The four cases of the experiment.

Cities are numbered 0, ..., n - 1 and city 0 is home: every route starts and
ends there. A distance matrix is a list of rows, d[i][j] in km (or in units of
the plane for the random cases).

- ``ivanov14``: the 14 cities of the case (Ivanov et al., 2025, Fig. 14.4),
  with Hamburg as city 0; the other cities keep the order of the case.
- ``random20``, ``random30``, ``random50``: n cities with coordinates drawn
  uniformly in [0, 500] x [0, 500] with ``random.Random(n)``, and Euclidean
  distances rounded to the nearest integer.
"""

from __future__ import annotations

import math
import random

from routes.data import CITIES, d as _d

# Seed of each random case: its number of cities
RANDOM_SIZES = (20, 30, 50)


def ivanov14() -> list[list[int]]:
    """Distance matrix of the case, Table 2 of traveling_salesman.md, renumbered from 0."""
    return [[_d[i][j] for j in CITIES] for i in CITIES]


def random_points(n: int, seed: int | None = None) -> list[tuple[float, float]]:
    """n points drawn uniformly in [0, 500] x [0, 500]."""
    rng = random.Random(n if seed is None else seed)
    return [(rng.uniform(0, 500), rng.uniform(0, 500)) for _ in range(n)]


def euclidean_matrix(points: list[tuple[float, float]]) -> list[list[int]]:
    """Euclidean distances rounded to the nearest integer."""
    return [[round(math.dist(p, q)) for q in points] for p in points]


def case(name: str) -> list[list[int]]:
    """Distance matrix of a case by name: 'ivanov14', 'random20', 'random30' or 'random50'."""
    if name == "ivanov14":
        return ivanov14()
    if name.startswith("random") and int(name[6:]) in RANDOM_SIZES:
        return euclidean_matrix(random_points(int(name[6:])))
    raise ValueError(f"Unknown case {name!r}")


CASES = ("ivanov14",) + tuple(f"random{n}" for n in RANDOM_SIZES)
