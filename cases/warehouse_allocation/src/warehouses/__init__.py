"""Which warehouse serves each customer: the T1 running example.

The data are in ``data``, the calculations in ``model`` and ``forecast``, and
what the notebook shows in ``show``. The notebook calls the functions below,
one per step:

1. ``show_data``: Tables 1-4 and the map;
2. ``check_plan``: any plan, on the map and against the capacities;
3. ``rule_of_thumb``, ``challenge`` and ``solve_model``: experience against the model (§3);
4. ``all_plans_table``, ``explosion_table`` and ``compare_methods``: how many plans (§4);
5. ``two_objectives``: cost and delivery time (§5);
6. ``show_forecast``, ``large_error`` and ``safety_margin``: uncertainty (§6).
"""

from . import data, forecast, model
from .show import (all_plans_table, challenge, check_plan, compare_methods, explosion_table,
                   large_error, rule_of_thumb, safety_margin, show_data, show_forecast,
                   solve_model, two_objectives)

__all__ = [
    "all_plans_table", "challenge", "check_plan", "compare_methods", "data", "explosion_table",
    "forecast", "large_error", "model", "rule_of_thumb", "safety_margin", "show_data",
    "show_forecast", "solve_model", "two_objectives",
]
