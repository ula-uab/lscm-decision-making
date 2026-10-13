"""How many tickets of each fare of each trip an airline puts on sale on two
connected flights: a linear network model and its bid prices.

The data are in ``data``, the rule «highest fare first», the model, the bid
prices, their ranges, the offer and the other aircraft in ``model``, and what
the notebook shows in ``show``. The notebook calls the functions below, one per
step:

1. ``show_data``: the flights, the trips and the fares (§1);
2. ``rule``: the plan of the rule «highest fare first» (§2);
3. ``optimal_plan``: the optimal plan against the rule, binding constraints and slack (§4);
4. ``bid_prices``: the bid prices of the flights and of the tickets (§5);
5. ``tour_operator_offer``: an offer of connecting seats (§7);
6. ``other_aircraft``: another aircraft on a flight (§8).
"""

from . import data, model
from .show import bid_prices, optimal_plan, other_aircraft, rule, show_data, tour_operator_offer

__all__ = ["bid_prices", "data", "model", "optimal_plan", "other_aircraft", "rule", "show_data",
           "tour_operator_offer"]
