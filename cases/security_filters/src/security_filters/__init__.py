"""Security filters case: passengers arriving at the airport security filters.

From the flight schedule of one day, the package computes how many passengers
arrive at the security filters in each 5-minute slot (the presentation
curve) and, for given filter capacities, the queue and the idle time of the
filters. Scenarios compare different assumptions on the same day.
"""

from .arrivals import hourly, presentation_curve, slot_labels
from .indicators import simulate_queue, summary
from .profiles import read_profiles
from .scenarios import (Scenario, capacity_by_hour, capacity_from_fraction,
                        capacity_from_lanes, compare, run)
from .schedule import days, flights_for_curve, flights_of_day, read_schedule

__all__ = [
    "Scenario", "capacity_by_hour", "capacity_from_fraction", "capacity_from_lanes",
    "compare", "days", "flights_for_curve", "flights_of_day", "hourly",
    "presentation_curve", "read_profiles", "read_schedule", "run",
    "simulate_queue", "slot_labels", "summary",
]
