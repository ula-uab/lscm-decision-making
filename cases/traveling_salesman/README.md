# Round trip of a sales representative through 14 cities

A sales representative leaves Hamburg, visits 13 other cities of northern Germany once each and returns to Hamburg. The case builds her route with two construction heuristics, the nearest neighbor (greedy) and the sweep (not greedy), and shortens it with a local search with two moves: the swap of two adjacent cities and the reversal of a sub-path. It calculates the shortest route exactly, by dynamic programming, to measure how far each heuristic is from it, and starts the local search from 20,000 random routes to show that where it stops depends on the move and on the starting route. The data are from Ivanov et al. (2025, §14.3).

The document [`traveling_salesman.md`](traveling_salesman.md) explains the case and has all its data and results.

## Notebook

| Notebook | Question | Open in Colab |
|---|---|---|
| [Round trip of a sales representative through 14 cities](notebooks/traveling_salesman.ipynb) | How good are the routes of two construction heuristics, and where does a local search that shortens them stop? | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ula-uab/lscm-decision-making/blob/main/cases/traveling_salesman/notebooks/traveling_salesman.ipynb) |

In Colab nothing has to be installed: the first cell installs the case. The cells have forms (drop-down lists, a tick box and a slider) to choose the starting route of the local search (nearest neighbor, sweep, or a random route with its seed) and the move, to see the search step by step on the map, and to set the number of random starting routes. Outside Colab the forms are plain lines such as `seed = 1`: edit the value and run the cell again.

## Files

| File | What it is |
|---|---|
| [`traveling_salesman.md`](traveling_salesman.md) | The document of the case |
| [`traveling_salesman_heuristics.py`](traveling_salesman_heuristics.py) | Script that prints the nearest neighbor, the sweep, the pass of Ivanov et al. and the local search, step by step, with each move. Needs only Python |
| [`traveling_salesman_local_optima.py`](traveling_salesman_local_optima.py) | Script that prints the shortest route, each heuristic against it and where the local search stops from random starting routes. Needs only Python |
| [`figures/`](figures/) | The maps of the document, drawn by the package |
| [`notebooks/`](notebooks/) | The notebook |
| [`src/routes/`](src/routes/) | The code the notebook calls: data, construction heuristics, local search, shortest route, tables and maps |
| [`tests/`](tests/) | Checks that the package gives the numbers of the document and that the notebook runs |

To draw the maps of the document again, from this folder and with the environment of the repository: `uv run python -c "import routes; routes.document_figures()"`.

Running the scripts or the notebook is optional: it is support material, not part of the assessment.
