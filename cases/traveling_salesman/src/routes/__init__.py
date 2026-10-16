"""The round trip of a sales representative through 14 cities of northern Germany.

The data are in ``data``; routes, their length and the two construction
heuristics in ``construction``; Ivanov's pass and the local search in
``local_search``; the shortest route by dynamic programming in ``exact``; and
what the notebook shows in ``show``. The notebook calls the functions below,
one per step:

1. ``show_data``: the cities, the distances and the number of routes (§1);
2. ``nearest_neighbor``: the greedy route from Hamburg (§3);
3. ``sweep``: the cities in the order of their angle seen from Hamburg (§4);
4. ``ivanov_pass`` and ``local_search_steps``: the pass of Ivanov et al. and the
   local search from any starting route with either move (§5);
5. ``shortest_route`` and ``local_optima``: the shortest route, and where the
   search stops from random starting routes (§6).
"""

from . import construction, data, exact, local_search
from .show import (document_figures, ivanov_pass, local_optima, local_search_steps, nearest_neighbor,
                   plot_route, shortest_route, show_data, sweep)

__all__ = [
    "construction", "data", "document_figures", "exact", "ivanov_pass", "local_optima", "local_search",
    "local_search_steps", "nearest_neighbor", "plot_route", "shortest_route", "show_data", "sweep",
]
