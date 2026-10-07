"""Security filters case: passengers arriving at the airport security checkpoint.

Workflow:

1. read the flights and select a day (``read_schedule``, ``flights_for_curve``);
2. build a demand scenario: select groups of flights and give them a load
   factor, a share of passengers in transit and an arrival pattern, and make
   arrival surges (``Scenario``, ``PATTERNS``; in the notebook, the panel of
   ``security_filters.panel``);
3. compute the PPP of the airport for the scenario (``airport_ppp``);
4. compare the PPPs of several scenarios of the same day (``compare``);
5. write a capacity plan: open lanes by period of the day (``CapacityPlan``);
6. the real PPP of each day (``real_ppp``), to check scenarios and plans against;
7. apply a plan to the real PPP: queue, unused capacity and waits (``apply_plan``);
8. passengers who miss the closing of their gate (``missed_with_scenario``,
   ``missed_with_real``).
"""

from .capacity import CapacityPlan
from .comparison import Comparison, compare
from .patterns import DEFAULT_PATTERN, PATTERNS, ArrivalPattern, erlang, normal
from .ppp import (GATE_SLOTS, N_SLOTS, PPP, airport_ppp, flight_passengers, hourly,
                  slot_labels, whole_passengers)
from .missed import MissedResult, missed_with_real, missed_with_scenario
from .queues import QueueResult, apply_plan
from .real import read_real_ppps, real_ppp
from .scenario import Scenario
from .schedule import (airlines, airports, days, flights_for_curve, flights_of_day,
                       read_flight_data, read_schedule)

__all__ = [
    "ArrivalPattern", "CapacityPlan", "Comparison", "DEFAULT_PATTERN", "GATE_SLOTS", "MissedResult",
    "N_SLOTS",
    "PATTERNS", "PPP", "QueueResult", "Scenario", "airlines", "airport_ppp", "airports",
    "apply_plan", "compare", "days", "erlang", "flight_passengers", "flights_for_curve",
    "missed_with_real", "missed_with_scenario",
    "flights_of_day", "hourly", "normal", "read_flight_data", "read_real_ppps",
    "read_schedule", "real_ppp", "slot_labels", "whole_passengers",
]
