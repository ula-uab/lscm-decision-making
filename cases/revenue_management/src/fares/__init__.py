"""How many tickets of each fare an airline puts on sale for a flight: a linear model.

The data are in ``data``, the model, its slacks, shadow prices, ranges and the
revenue against capacity in ``model``, and what the notebook shows in ``show``.
The notebook calls the functions below, one per step:

1. ``show_data``: the fares and the revenue per seat of each one (§1);
2. ``optimal_plan``: the optimal plan and its binding constraints (§3);
3. ``shadow_prices``: the shadow prices, one checked by solving again (§4);
4. ``revenue_against_capacity``: the revenue curve and the ranges (§5, §6);
5. ``other_capacity``: another aircraft, solved again and estimated with the bid price (§7).
"""

from . import data, model
from .show import optimal_plan, other_capacity, revenue_against_capacity, shadow_prices, show_data

__all__ = ["data", "model", "optimal_plan", "other_capacity", "revenue_against_capacity",
           "shadow_prices", "show_data"]
