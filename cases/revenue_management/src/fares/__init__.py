"""How many tickets of each fare of each trip an airline puts on sale on two
connected flights: a linear network model and its bid prices.

The data are in ``data``, the model, the bid prices, the shadow prices of the
forecast demand, their ranges, the offer and a change in the demand of a fare in
``model``, and what the notebook shows in ``show``. The notebook calls the
functions below, one per step:

1. ``show_data``: the flights, the trips and the fares (§1);
2. ``optimal_plan``: the optimal plan, binding constraints and slack (§2);
3. ``bid_prices``: the bid prices of the flights and of the tickets, and their ranges (§3);
4. ``tour_operator_offer``: an offer of connecting seats (§4);
5. ``demand_change``: a change in the forecast demand of a fare (§5).
"""

from . import data, model
from .show import bid_prices, demand_change, optimal_plan, show_data, tour_operator_offer

__all__ = ["bid_prices", "data", "demand_change", "model", "optimal_plan", "show_data",
           "tour_operator_offer"]
