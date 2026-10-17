# Genetic and memetic algorithms against repeated local search

An experiment on the route of the case and on three random cases: how a genetic
algorithm with crossovers suited to routes, and a memetic algorithm, compare
with local search repeated from random routes, for the same number of routes
evaluated. It is not part of the case document.

## Methods

| Id | Method |
|---|---|
| LS1 | Local search from one random route |
| LSR | Local search from random routes, one after another, keeping the best, until the budget is used |
| GA-KF | Genetic algorithm with one-point crossover for sequences and exchange mutation (Klein and Faust, 2015, §31.4) |
| GA-ER | Genetic algorithm with edge recombination crossover, ER (Larrañaga et al., 1999, §4.3.7), and inversion mutation, IVM (§4.3.16) |
| GA-OX | Genetic algorithm with order crossover, OX1 (Larrañaga et al., 1999, §4.3.3), and IVM |
| MA-ER | GA-ER with local search on every new individual (Klein and Faust, 2015, §31.5) |

The local search is the one of the case: reversal of a sub-path, best
improvement. Genetic algorithms: tournament of 2 and elitism; population 50
(10 in MA-ER); probability of crossover 0.9; probability of mutation of an
individual 1/n, with n the number of cities. An evaluation is the length of a
route or the change in length of a move. Budget of each case, the same for
every method: 85,000 (14 cities), 300,000 (20), 1,000,000 (30) and 5,400,000 (50)
evaluations. 30 runs of each method on each case, with seeds 1 to 30.

## Cases

- The 14 cities of the case (Ivanov et al., 2025, Fig. 14.4).
- 20, 30 and 50 cities with coordinates drawn uniformly in [0, 500] x [0, 500]
  (seed: the number of cities) and Euclidean distances rounded to the integer.

The shortest route of each case is computed exactly with an integer model
solved by HiGHS, adding constraints against subtours until the solution is a
single route.

## Files

| File | Content |
|---|---|
| `instances.py` | The four cases |
| `operators.py` | Crossovers, mutations and tournament; OX1 is `cxOrdered` of DEAP 1.4.4 |
| `methods.py` | Local search with a budget, and the six methods |
| `exact.py` | Shortest route with PuLP and HiGHS |
| `run_experiment.py` | Runs everything and writes `results/` |
| `test_experiments.py` | The operators against the examples of their sources, the local search against the case, the shortest route of the 14 cities |
| `results/` | `summary.md` (one table per case), `runs.csv` (every run), `shortest_routes.csv`, `curves_ivanov14.json` and `curve_ivanov14.png` |

## How to run it

From the root of the repository (DEAP is not a dependency of the case, so
`uv` adds it only for these commands):

```
uv run --with deap==1.4.4 pytest cases/traveling_salesman/experiments
uv run --with deap==1.4.4 python cases/traveling_salesman/experiments/run_experiment.py
```

The whole experiment takes about 15 minutes on 10 cores. `--cases`, `--runs`
and `--workers` run a part of it.

## References

Ivanov, D., Tsipoulanidis, A., & Schönberger, J. (2025). *Global supply chain and operations management: A decision-oriented introduction to the creation of value* (4th ed.). Springer. https://doi.org/10.1007/978-3-031-95859-5

Klein, R., & Faust, O. (2015). Genetic algorithms. In H. Stadtler, C. Kilger, & H. Meyr (Eds.), *Supply chain management and advanced planning: Concepts, models, software, and case studies* (5th ed., pp. 537–544). Springer. https://doi.org/10.1007/978-3-642-55309-7

Larrañaga, P., Kuijpers, C. M. H., Murga, R. H., Inza, I., & Dizdarevic, S. (1999). Genetic algorithms for the travelling salesman problem: A review of representations and operators. *Artificial Intelligence Review, 13*(2), 129–170. https://doi.org/10.1023/A:1006529012972
