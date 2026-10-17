"""The six methods of the experiment, all with the same budget of evaluations.

An evaluation is computing the length of a route or the change in length of a
move of the local search. Each method stops as soon as it has used its budget,
even in the middle of a local search, and returns the shortest route found.

| Id    | Method |
|-------|--------|
| LS1   | Local search from one random route |
| LSR   | Local search from random routes, one after another, keeping the best, until the budget is used |
| GA-KF | Genetic algorithm with one-point crossover and exchange mutation (Klein and Faust, 2015, §31.4) |
| GA-ER | Genetic algorithm with ER crossover and IVM (Larrañaga et al., 1999, §4.3.7 and §4.3.16) |
| GA-OX | Genetic algorithm with OX1 crossover and IVM (Larrañaga et al., 1999, §4.3.3 and §4.3.16) |
| MA-ER | GA-ER with local search on every new individual (Klein and Faust, 2015, §31.5) |

The local search is the one of the case: reversal of a sub-path, best
improvement, ties to the first move in the order of evaluation (i increasing
and, for each i, j increasing).
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field

import operators as op

METHODS = ("LS1", "LSR", "GA-KF", "GA-ER", "GA-OX", "MA-ER")

# Parameters (Klein and Faust, 2015, §31.2-§31.4)
POPULATION = 50          # genetic algorithms
POPULATION_MEMETIC = 10  # memetic algorithm: each new individual costs a local search
CROSSOVER = 0.9          # probability of crossover of a pair
TOURNAMENT = 2           # individuals per group of the tournament
# Probability of mutation of an individual: 1/n, with n the number of cities


class BudgetUsed(Exception):
    """Raised when a method has used its budget of evaluations."""


@dataclass
class Tracker:
    """Counts evaluations, keeps the shortest route found and the curve of its
    length against the evaluations made."""
    d: list[list[int]]
    budget: int
    evaluations: int = 0
    best: int | None = None
    best_route: list[int] | None = None
    curve: list[tuple[int, int]] = field(default_factory=list)

    def found(self, route: list[int], length: int) -> None:
        if self.best is None or length < self.best:
            self.best, self.best_route = length, list(route)
            self.curve.append((self.evaluations, length))

    def evaluate(self, route: list[int]) -> int:
        """Length of a route (open list of the n cities): one evaluation."""
        if self.evaluations >= self.budget:
            raise BudgetUsed
        self.evaluations += 1
        d = self.d
        length = d[route[-1]][route[0]] + sum(d[a][b] for a, b in zip(route, route[1:]))
        self.found(route, length)
        return length


def local_search(route: list[int], length: int, t: Tracker) -> tuple[list[int], int]:
    """Local search with the reversal of a sub-path and best improvement, from a
    route (open list starting at home) whose length is already known.

    Reversing positions i to j of the closed route takes out the arcs (i - 1, i)
    and (j, j + 1) and puts in (i - 1, j) and (i, j + 1), so the change in
    length uses four distances. The moves are 1 <= i < j <= n - 1: home stays
    at position 0. Each move evaluated is one evaluation; if the budget runs out
    in the middle of a scan, the search stops without making a move."""
    d = t.d
    r = list(route) + [route[0]]
    n = len(route)
    while True:
        left = t.budget - t.evaluations
        if left <= 0:
            raise BudgetUsed
        best, bi, bj, done = 0, -1, -1, 0
        cut = False
        for i in range(1, n - 1):
            a, b = r[i - 1], r[i]
            da, db = d[a], d[b]
            dab = da[b]
            last = n - 1  # last j
            if done + (last - i) > left:
                last = i + (left - done)
                cut = True
            for j in range(i + 1, last + 1):
                c, e = r[j], r[j + 1]
                delta = da[c] + db[e] - dab - d[c][e]
                if delta < best:
                    best, bi, bj = delta, i, j
            done += last - i
            if cut:
                break
        t.evaluations += done
        if cut:
            raise BudgetUsed
        if bi < 0:
            return r[:-1], length
        r[bi:bj + 1] = r[bi:bj + 1][::-1]
        length += best
        t.found(r[:-1], length)


def random_route(n: int) -> list[int]:
    """Home (0) and the other cities in random order."""
    rest = list(range(1, n))
    random.shuffle(rest)
    return [0] + rest


def ls1(t: Tracker, n: int) -> None:
    route = random_route(n)
    local_search(route, t.evaluate(route), t)


def lsr(t: Tracker, n: int) -> None:
    while True:
        route = random_route(n)
        local_search(route, t.evaluate(route), t)


CROSS = {"GA-KF": op.one_point, "GA-ER": op.er_pair, "GA-OX": op.ox1, "MA-ER": op.er_pair}
MUTATE = {"GA-KF": op.exchange, "GA-ER": op.ivm, "GA-OX": op.ivm, "MA-ER": op.ivm}


def genetic(t: Tracker, n: int, method: str) -> None:
    """Generational genetic algorithm (Klein and Faust, 2015, §31.1-§31.4):

    1. random initial population (with local search in MA-ER);
    2. gene pool of P individuals by tournament of 2;
    3. the pool is taken in pairs; each pair is recombined into two children
       with probability 0.9, or copied;
    4. each child is mutated with probability 1/n;
    5. each new child (recombined or mutated) is evaluated; in MA-ER it is
       replaced by the local optimum that the local search reaches from it
       (Lamarckian, §31.5). Copies keep the length of their parent;
    6. elitism: the shortest route of the old population replaces the longest
       route of the new one.
    """
    memetic = method.startswith("MA")
    size = POPULATION_MEMETIC if memetic else POPULATION
    cross, mutate = CROSS[method], MUTATE[method]

    def evaluate(route: list[int]) -> tuple[list[int], int]:
        length = t.evaluate(route)
        return local_search(route, length, t) if memetic else (route, length)

    pop, lengths = [], []
    for _ in range(size):
        route, length = evaluate(random_route(n))
        pop.append(route)
        lengths.append(length)
    while True:
        pool = op.tournament(lengths, size, TOURNAMENT)
        children = []
        for k in range(0, size, 2):
            x, y = pool[k], pool[k + 1]
            if random.random() < CROSSOVER:
                pair = [[op.rotate(c), None] for c in cross(pop[x], pop[y])]
            else:
                pair = [[pop[x], lengths[x]], [pop[y], lengths[y]]]
            for child in pair:
                if random.random() < 1 / n:
                    child[:] = [op.rotate(mutate(child[0])), None]
            children += pair
        for child in children:
            if child[1] is None:
                child[:] = list(evaluate(child[0]))
        elite = min(range(size), key=lambda i: lengths[i])
        worst = max(range(size), key=lambda i: children[i][1])
        children[worst] = [pop[elite], lengths[elite]]
        pop = [c[0] for c in children]
        lengths = [c[1] for c in children]


def run(method: str, d: list[list[int]], budget: int, seed: int) -> dict:
    """One run of a method on a case: shortest length, evaluations used, CPU
    time (s) and the curve of the best length against the evaluations."""
    random.seed(seed)
    t = Tracker(d, budget)
    n = len(d)
    start = time.process_time()
    try:
        if method == "LS1":
            ls1(t, n)
        elif method == "LSR":
            lsr(t, n)
        else:
            genetic(t, n, method)
    except BudgetUsed:
        pass
    return {"method": method, "seed": seed, "best": t.best, "route": t.best_route,
            "evaluations": t.evaluations, "seconds": time.process_time() - start, "curve": t.curve}
