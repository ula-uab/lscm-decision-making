"""Which suppliers to contract and which supplier each component is bought from.

The data are in ``data``; the decision matrix in ``matrix``; selections and their
cost, without a solver, in ``selection`` and ``local_search``; the integer model,
its relaxation and branch and bound in ``model``; and what the notebook shows in
``show``. The notebook calls the functions below, one per step:

1. ``show_data``: prices, annual costs, fixed cost and scorecard;
2. ``batteries_matrix``: the decision matrix of the batteries, with the price (§3);
3. ``buyer_rule`` and ``check_selection``: the buyer's rule and any selection (§4);
4. ``count_selections`` and ``solve_model``: how many selections, and the optimum (§5);
5. ``local_search_steps``: the local search from any selection (§6);
6. ``reduced_data``, ``relaxation`` and ``branch_and_bound``: how an integer model is solved (§7).
"""

from . import data, local_search, matrix, model, selection
from .show import (batteries_matrix, branch_and_bound, buyer_rule, check_selection, count_selections,
                   local_search_steps, reduced_data, relaxation, selections_table, show_data, solve_model,
                   tree_table)

__all__ = [
    "batteries_matrix", "branch_and_bound", "buyer_rule", "check_selection", "count_selections", "data",
    "local_search", "local_search_steps", "matrix", "model", "reduced_data", "relaxation", "selection",
    "selections_table", "show_data", "solve_model", "tree_table",
]
