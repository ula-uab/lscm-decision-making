"""How many bikes each plant assembles each month: a linear model.

The data are in ``data``, the model, its shadow prices, reduced costs and ranges
in ``model``, and what the notebook shows in ``show``. The notebook calls the
functions below, one per step:

1. ``show_data``: the plants and the two demand forecasts;
2. ``feasible_region``: the reduced version, two plants and one month (§3);
3. ``production_plan``: the plan of the full case for a forecast (§4, §5);
4. ``capacity_and_demand``: capacity against demand, month by month and cumulative (§5).

Each later version of the model has a module of its own, with its model and what
its notebook shows: ``plant_stock`` (M1, stock at the plants),
``central_warehouse`` (M2, central warehouse and backorders),
``distribution_network`` (M3, distribution network) and ``retailers`` (M4,
retailers, backorder shares and lost sales). ``capacity_scenarios`` (M4B) is a
version of its own, built on M4: a demand growth and a price by month, overtime,
rented storage and a plant open or closed. ``lot_sizing`` takes the master plan
of M4 to the weekly lot plan of each plant, by bike model. ``expanded_network``
is the network after an expansion, with three selection problems: which local
warehouse serves each retailer, which sites act as regional warehouses, and the
weekly routes of one local warehouse.
"""

from . import (capacity_scenarios, central_warehouse, data, distribution_network, expanded_network, lot_sizing, model,
               plant_stock, retailers)
from .show import capacity_and_demand, feasible_region, production_plan, show_data

__all__ = ["capacity_and_demand", "capacity_scenarios", "central_warehouse", "data", "distribution_network",
           "expanded_network", "feasible_region", "lot_sizing", "model", "plant_stock", "production_plan", "retailers", "show_data"]
