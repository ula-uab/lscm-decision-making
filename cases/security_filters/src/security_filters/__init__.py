"""Security filters case: passengers arriving at the airport security filters.

Workflow:

1. read the flight schedule and select a day (``read_schedule``,
   ``flights_for_curve``);
2. write the assumptions on the flights as rules and group them in demand
   scenarios (``DemandScenario``); each scenario gives a presentation curve
   (``demand_curves``);
3. define lane policies, the open lanes in each period of the day
   (``LanePlan``), and evaluate them on the scenario curves
   (``decision_table``);
4. after the day, compare the scenarios and the policies with the observed
   curve (``read_observed``, ``compare_forecasts``).
"""

from . import examples
from .arrivals import hourly, presentation_curve, slot_labels
from .assumptions import apply_rules, read_rules, summary_by_airline
from .distributions import PRESETS, ArrivalPattern, describe, gamma_profile, profile_library
from .indicators import simulate_queue, summary
from .observed import compare_forecasts, forecast_errors, read_observed
from .policies import (LanePlan, capacity_by_hour, capacity_from_fraction, capacity_from_lanes,
                       decision_table, evaluate, evaluate_all, lanes_to_cover, regret, worst_case)
from .profiles import read_profiles
from .scenarios import DemandScenario, demand_curves
from .schedule import days, flights_for_curve, flights_of_day, read_schedule

__all__ = [
    "ArrivalPattern", "DemandScenario", "examples", "LanePlan", "PRESETS", "apply_rules",
    "capacity_by_hour", "capacity_from_fraction", "capacity_from_lanes",
    "compare_forecasts", "days", "decision_table", "demand_curves", "describe",
    "evaluate", "evaluate_all", "flights_for_curve", "flights_of_day",
    "forecast_errors", "gamma_profile", "hourly", "lanes_to_cover",
    "presentation_curve", "profile_library", "read_observed", "read_profiles",
    "read_rules", "read_schedule", "regret", "simulate_queue", "slot_labels",
    "summary", "summary_by_airline", "worst_case",
]
