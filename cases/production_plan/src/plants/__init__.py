"""How many bikes each plant assembles each month: a linear model.

The data are in ``data``, the model, its shadow prices, reduced costs and ranges
in ``model``, and what the notebook shows in ``show``. The notebook calls the
functions below, one per step:

1. ``show_data``: the plants and the two demand forecasts;
2. ``feasible_region``: the reduced version, two plants and one month (§3);
3. ``production_plan``: the plan of the full case for a forecast (§4, §5);
4. ``capacity_and_demand``: capacity against demand, month by month and cumulative (§5).
"""

from . import data, model
from .show import capacity_and_demand, feasible_region, production_plan, show_data

__all__ = ["capacity_and_demand", "data", "feasible_region", "model", "production_plan", "show_data"]
