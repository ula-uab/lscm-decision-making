"""A genetic algorithm for the route (§6 of the notebook).

A route is coded as a chromosome: the list of the 13 cities in the order of
visit. Hamburg is left out, because every route starts and ends there; each
city appears once. Positions are counted from 0 in the code; the notebook
counts them from 1.

Two operators, from Larrañaga et al. (1999):

- **order crossover** (§4.3.3): two cuts are chosen. Each child copies the
  cities between the cuts of one parent, in the same positions, and fills the
  other positions with the missing cities in the order in which they appear in
  the other parent, starting just after the second cut and going round to the
  beginning;
- **inversion mutation** (§4.3.16): a sub-path of consecutive cities is taken
  out of the route, reversed and put back somewhere else.

The genetic algorithm: random initial population; parents chosen by a
tournament of two; order crossover with probability 0.9; inversion mutation of
each child with a given probability; optionally, local search with the
reversal of a sub-path on every new route; the shortest route of the previous
generation replaces the longest of the new one.
"""

from __future__ import annotations

import random

from . import construction as co
from . import local_search as ls
from .data import CITIES, HOME

CROSSOVER = 0.9  # probability that a pair of parents is recombined


def chromosome(route: list[int]) -> list[int]:
    """The 13 cities of a route, without Hamburg at both ends."""
    return route[1:-1]


def route(chromosome: list[int]) -> list[int]:
    """The route of a chromosome: from Hamburg and back."""
    return [HOME] + list(chromosome) + [HOME]


def length(chromosome: list[int]) -> int:
    """Length of the route of a chromosome (km)."""
    return co.length(route(chromosome))


def order_crossover(x: list[int], y: list[int], cut_1: int, cut_2: int) -> list[int]:
    """The child that copies x between the cuts (after position cut_1 and after
    position cut_2, so positions cut_1 to cut_2 - 1 counted from 0) and takes
    the other cities in the order of y, from just after the second cut."""
    n = len(x)
    copied = x[cut_1:cut_2]
    kept = set(copied)
    others = [c for c in (y[(cut_2 + k) % n] for k in range(n)) if c not in kept]
    child = [None] * n
    child[cut_1:cut_2] = copied
    for k, city in enumerate(others):
        child[(cut_2 + k) % n] = city
    return child


def crossover(x: list[int], y: list[int], cut_1: int, cut_2: int) -> tuple[list[int], list[int]]:
    """The two children of the order crossover: the first copies x between the
    cuts, the second copies y."""
    return order_crossover(x, y, cut_1, cut_2), order_crossover(y, x, cut_1, cut_2)


def inversion_mutation(chromosome: list[int], first: int, last: int, at: int) -> list[int]:
    """Take out the cities from position first to position last, reverse them
    and put them back after the first ``at`` cities of what is left."""
    sub_path = chromosome[first:last + 1]
    rest = chromosome[:first] + chromosome[last + 1:]
    return rest[:at] + sub_path[::-1] + rest[at:]


def mutations(n: int = 13, sizes=(2, 3, 4)) -> list[tuple[int, int, int]]:
    """Every inversion mutation of a chromosome of n cities with a sub-path of
    one of ``sizes`` cities, as (first, last, at), put back anywhere except the
    place it was taken from (that is a reversal of a sub-path, section 4)."""
    return [(first, first + k - 1, at) for k in sizes for first in range(n - k + 1)
            for at in range(n - k + 1) if at != first]


def mutations_that_lengthen(chromosome: list[int], sizes=(2, 3, 4)) -> tuple[int, int]:
    """How many of the mutations of ``mutations`` make the route longer, and how many there are."""
    before = length(chromosome)
    every = mutations(len(chromosome), sizes)
    longer = sum(length(inversion_mutation(chromosome, *m)) > before for m in every)
    return longer, len(every)


def _random_mutation(chromosome: list[int], rng: random.Random) -> list[int]:
    """Inversion mutation of a sub-path between two positions drawn at random,
    put back at a place drawn at random."""
    first, last = sorted(rng.sample(range(len(chromosome)), 2))
    at = rng.randint(0, len(chromosome) - (last - first + 1))
    return inversion_mutation(chromosome, first, last, at)


def _improve(c: list[int]) -> list[int]:
    """The local optimum of the local search with the reversal of a sub-path and best improvement."""
    return ls.local_optimum(route(c), "reversal")[1:-1]


def genetic_algorithm(population: int = 30, generations: int = 60, mutation: float = 0.1,
                      local_search: bool = False, seed: int = 1) -> dict:
    """Run the genetic algorithm. Returns, for each generation (0 is the initial
    population), the length of the shortest route and the mean length of the
    population, and the shortest route found."""
    rng = random.Random(seed)
    n = len(CITIES) - 1

    def new(c: list[int]) -> tuple[list[int], int]:
        c = _improve(c) if local_search else c
        return c, length(c)

    pop = []
    for _ in range(population):
        c = chromosome(co.random_route(rng=rng))
        pop.append(new(c))
    best, mean = [min(p[1] for p in pop)], [sum(p[1] for p in pop) / population]
    for _ in range(generations):
        def parent():
            a, b = rng.sample(range(population), 2)
            return pop[a] if pop[a][1] <= pop[b][1] else pop[b]
        children = []
        while len(children) < population:
            x, y = parent(), parent()
            if rng.random() < CROSSOVER:
                cut_1, cut_2 = sorted(rng.sample(range(n + 1), 2))
                pair = [[c, None] for c in crossover(x[0], y[0], cut_1, cut_2)]
            else:
                pair = [list(x), list(y)]
            for child in pair:
                if rng.random() < mutation:
                    child[:] = [_random_mutation(child[0], rng), None]
                if child[1] is None:
                    child[:] = list(new(child[0]))
            children += [tuple(c) for c in pair]
        children = children[:population]
        elite = min(pop, key=lambda p: p[1])
        worst = max(range(population), key=lambda k: children[k][1])
        children[worst] = elite
        pop = children
        best.append(min(p[1] for p in pop))
        mean.append(sum(p[1] for p in pop) / population)
    winner = min(pop, key=lambda p: p[1])
    return {"best": best, "mean": mean, "route": route(winner[0]), "length": winner[1]}
