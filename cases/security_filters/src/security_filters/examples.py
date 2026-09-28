"""Example demand scenarios and lane policies used in the notebooks.

They are a starting point: the notebooks show how they are written, and
students change them or write their own. The groups of airports and
airlines are illustrative.
"""

from __future__ import annotations

import pandas as pd

from .policies import LanePlan, lanes_to_cover
from .scenarios import DemandScenario

DAY = "2008-07-19"

BUSINESS_DESTINATIONS = ["MAD", "BCN", "BIO", "VLC", "SVQ", "AGP", "LIS", "CDG", "ORY",
                         "FRA", "MUC", "ZRH", "GVA", "BRU", "AMS", "FCO", "MXP", "LHR"]
LOW_COST_AIRLINES = ["RYR", "EZY", "VLG", "GWI", "BER", "NLY", "TCX"]
HUB_AIRLINES = ["AEA", "IBE"]  # many passengers connect at their hub
UK_AIRPORTS = ["LGW", "LHR", "LTN", "STN", "MAN", "BHX", "EMA", "NCL", "GLA", "EDI",
               "BRS", "CWL", "LPL", "LBA", "BOH", "EXT", "SOU", "NWI", "DSA", "MME"]

PERIODS = ["00:00-02:00", "02:00-05:00", "05:00-10:00", "10:00-14:00",
           "14:00-19:00", "19:00-24:00"]


def demand_scenarios() -> list[DemandScenario]:
    """Three scenarios, from the simplest to the most detailed."""
    base = DemandScenario(
        "base",
        [{"load_factor": 0.85, "profile": "leisure"}],
        "Every flight 85 % full, holiday passengers")

    by_type = DemandScenario(
        "by flight type",
        [{"load_factor": 0.85, "profile": "leisure"},
         {"destination": BUSINESS_DESTINATIONS, "profile": "business"},
         {"airline": LOW_COST_AIRLINES, "load_factor": 0.90, "profile": "low_cost"},
         {"airline": HUB_AIRLINES, "load_factor": 0.80, "transfer_share": 0.30},
         {"airline": "TOM", "load_factor": 0.95, "profile": "wave", "advance_min": 55}],
        "Profile by type of flight, connections at hubs, tour-operator buses")

    cruise = DemandScenario(
        "cruise day",
        by_type.rules + [
            {"destination": UK_AIRPORTS, "departure_from": "16:00", "departure_to": "18:00",
             "profile": "wave", "advance_min": 145}],
        "As 'by flight type', plus a cruise ship whose passengers to the UK "
        "(flights 16:00-18:00) arrive together by bus around 13:00")

    return [base, by_type, cruise]


def lane_policies(curves: pd.DataFrame) -> list[LanePlan]:
    """Four policies: open many lanes all day, or follow one scenario."""
    policies = [LanePlan("flat 28", {"02:00-23:00": 28}, default_lanes=4)]
    for scenario in curves:
        periods = lanes_to_cover(curves[scenario], PERIODS, quantile=0.8)
        policies.append(LanePlan(f"plan for {scenario}", periods))
    return policies
