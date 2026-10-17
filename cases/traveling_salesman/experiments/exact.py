"""Shortest route of a case, computed exactly with an integer model solved by HiGHS.

Model (symmetric distances): x[i, j] = 1 if the route uses the edge between
cities i and j (i < j). Minimise the sum of d[i][j] x[i, j], with two edges at
every city. The model is solved, the subtours of its solution are found, and a
constraint that forbids each subtour S is added: at most |S| - 1 edges with
both ends in S. This is repeated until the solution is a single route.
"""

from __future__ import annotations

import time

import pulp


def _optimal(result) -> bool:
    """PuLP 3 returns the status as a number and PuLP 4 as an object with a field status."""
    return getattr(result, "status", result) == 1


def _subtours(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    near = {i: [] for i in range(n)}
    for i, j in edges:
        near[i].append(j)
        near[j].append(i)
    seen, tours = set(), []
    for s in range(n):
        if s in seen:
            continue
        tour, stack = [], [s]
        while stack:
            c = stack.pop()
            if c in seen:
                continue
            seen.add(c)
            tour.append(c)
            stack += near[c]
        tours.append(tour)
    return tours


def shortest(d: list[list[int]], time_limit: float = 3600) -> dict:
    """Length and route of the shortest route, number of rounds and of subtour
    constraints added, and time (s)."""
    n = len(d)
    start = time.time()
    model = pulp.LpProblem("tsp", pulp.LpMinimize)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    x = {p: model.add_variable(f"x_{p[0]}_{p[1]}", lowBound=0, upBound=1, cat="Integer") for p in pairs}
    model += pulp.lpSum(d[i][j] * x[i, j] for i, j in pairs)
    for c in range(n):
        model += pulp.lpSum(x[p] for p in pairs if c in p) == 2
    rounds = cuts = 0
    while True:
        rounds += 1
        left = time_limit - (time.time() - start)
        if left <= 0 or not _optimal(model.solve(pulp.HiGHS(msg=False, timeLimit=left))):
            raise RuntimeError("HiGHS did not find the optimum within the time limit")
        used = [p for p in pairs if x[p].value() > 0.5]
        tours = _subtours(n, used)
        if len(tours) == 1:
            break
        for s in tours:
            inside = set(s)
            model += pulp.lpSum(x[i, j] for i, j in pairs if i in inside and j in inside) <= len(s) - 1
            cuts += 1
    route, prev = [0], None
    near = {i: [j for p in used for j in p if i in p and j != i] for i in range(n)}
    while len(route) < n:
        nxt = [c for c in near[route[-1]] if c != prev][0]
        prev = route[-1]
        route.append(nxt)
    length = sum(d[a][b] for a, b in zip(route, route[1:] + route[:1]))
    return {"length": length, "route": route, "rounds": rounds, "cuts": cuts,
            "seconds": time.time() - start}
