"""Which warehouse serves each customer: the T1 running example.

The data are in ``data``, the calculations in ``model`` and ``forecast``, and
what the notebook shows in ``show``. The notebook calls the functions below,
one per step:

1. ``show_data``: Tables 1-4 and the map;
2. ``check_plan``: any plan, on the map and against the capacities;
3. ``rule_of_thumb``, ``challenge`` and ``solve_model``: experience against the model (§3);
4. ``all_plans_table``, ``explosion_table`` and ``compare_methods``: how many plans (§4);
5. ``pareto`` and ``two_objectives``: cost and delivery time (§5);
6. ``show_forecast``, ``large_error`` and ``safety_margin``: uncertainty (§6);
7. ``show_orders``, ``plan_by_week``, ``customer_forecast`` and ``period_costs``: plans
   under uncertain demand (§7, functions in ``uncertain``).
"""

from . import data, forecast, model, uncertain
from .show import (all_plans_table, challenge, check_plan, compare_methods, customer_forecast,
                   explosion_table, large_error, pareto, pareto_table, period_cost_table, period_costs,
                   plan_by_week, rule_of_thumb, safety_margin, show_data, show_forecast, show_orders,
                   solve_model, summary_table, two_objectives)

__all__ = [
    "all_plans_table", "challenge", "check_plan", "compare_methods", "data", "explosion_table",
    "forecast", "large_error", "model", "pareto", "pareto_table", "rule_of_thumb", "safety_margin", "show_data",
    "show_forecast", "solve_model", "two_objectives", "uncertain", "show_orders", "plan_by_week",
    "customer_forecast", "period_costs", "period_cost_table", "summary_table",
]
