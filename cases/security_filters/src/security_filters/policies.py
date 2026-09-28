"""Lane policies: how many security lanes are open in each period of the day.

A policy is the decision: the number of open lanes in each period. With the
capacity of one lane (passengers per hour) it gives the capacity of the
filters in each 5-minute slot. Evaluating several policies on the curves of
several demand scenarios gives a decision table: one row per policy, one
column per scenario.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .indicators import simulate_queue, summary
from .scenarios import _check_unique
from .schedule import SLOT_MINUTES, SLOTS_PER_DAY

SLOTS_PER_HOUR = 60 // SLOT_MINUTES
DEFAULT_PAX_PER_LANE_HOUR = 180  # provisional value, to be validated


@dataclass
class LanePlan:
    """Open lanes by period.

    ``periods`` maps ``"HH:MM-HH:MM"`` (start included, end excluded; the day
    ends at ``"24:00"``) to a number of lanes, for example
    ``{"02:00-06:00": 20, "06:00-12:00": 32}``. Slots outside every period
    have ``default_lanes``. If periods overlap, the later one wins.
    """
    name: str
    periods: dict[str, int]
    pax_per_lane_hour: float = DEFAULT_PAX_PER_LANE_HOUR
    default_lanes: int = 0

    def lanes(self) -> np.ndarray:
        """Open lanes in each of the 288 slots."""
        lanes = np.full(SLOTS_PER_DAY, self.default_lanes, dtype=float)
        for period, n in self.periods.items():
            start, end = _period_slots(period)
            lanes[start:end] = n
        return lanes

    def capacity(self) -> np.ndarray:
        """Passengers the filters can serve in each slot."""
        return self.lanes() * self.pax_per_lane_hour / SLOTS_PER_HOUR

    def lane_hours(self) -> float:
        """Lane-hours of the day: the cost of the policy in staff time."""
        return self.lanes().sum() / SLOTS_PER_HOUR


def evaluate(policy: LanePlan, curve: pd.Series) -> pd.Series:
    """Indicators of a policy on one presentation curve, with its lane-hours."""
    result = simulate_queue(curve.to_numpy(), policy.capacity())
    return pd.concat([pd.Series({"lane_hours": policy.lane_hours()}), summary(result)])


def evaluate_all(policies: list[LanePlan], curves: pd.DataFrame) -> pd.DataFrame:
    """Every indicator of every policy on every scenario (long table)."""
    _check_unique([p.name for p in policies], "policy")
    _check_unique(list(curves.columns), "scenario")
    rows = []
    for policy in policies:
        for scenario in curves:
            indicators = evaluate(policy, curves[scenario])
            rows.append({"policy": policy.name, "scenario": scenario, **indicators.to_dict()})
    return pd.DataFrame(rows)


def decision_table(policies: list[LanePlan], curves: pd.DataFrame,
                   indicator: str = "average_wait_min") -> pd.DataFrame:
    """One indicator, one row per policy and one column per scenario.

    A column ``lane_hours`` is added: it does not depend on the scenario.
    """
    table = evaluate_all(policies, curves)
    wide = table.pivot(index="policy", columns="scenario", values=indicator)
    wide = wide.loc[[p.name for p in policies], list(curves.columns)]
    wide.insert(0, "lane_hours", [p.lane_hours() for p in policies])
    return wide


def worst_case(table: pd.DataFrame) -> pd.Series:
    """Worst value of each policy over the scenarios (lower is better)."""
    return table.drop(columns="lane_hours", errors="ignore").max(axis=1).rename("worst_case")


def regret(table: pd.DataFrame) -> pd.DataFrame:
    """Regret: how much worse each policy is than the best one in each
    scenario (lower is better). The last column is the maximum regret."""
    values = table.drop(columns="lane_hours", errors="ignore")
    result = values - values.min(axis=0)
    result["max_regret"] = result.max(axis=1)
    return result


def lanes_to_cover(curve: pd.Series, periods: list[str],
                   pax_per_lane_hour: float = DEFAULT_PAX_PER_LANE_HOUR,
                   quantile: float = 1.0) -> dict[str, int]:
    """A first guess of a policy: in each period, the lanes needed so that the
    capacity covers the arrivals of the busiest slot (or of the given
    quantile of the slots) of that period. It ignores the queue, so it is a
    starting point to adjust, not an optimum."""
    per_lane_slot = pax_per_lane_hour / SLOTS_PER_HOUR
    guess = {}
    for period in periods:
        start, end = _period_slots(period)
        arrivals = curve.iloc[start:end].quantile(quantile)
        guess[period] = int(math.ceil(arrivals / per_lane_slot))
    return guess


# --- Other ways of giving the capacity directly -------------------------------

def capacity_from_fraction(fraction, max_capacity: float = 500) -> np.ndarray:
    """Capacity as a fraction of the maximum, as in the original workbook
    (sheet "Hipotesis": fraction x 500 passengers per slot)."""
    return np.asarray(fraction, dtype=float) * max_capacity


def capacity_from_lanes(open_lanes, pax_per_lane_hour: float = DEFAULT_PAX_PER_LANE_HOUR) -> np.ndarray:
    """Capacity per slot from the number of open lanes in each slot."""
    return np.asarray(open_lanes, dtype=float) * pax_per_lane_hour / SLOTS_PER_HOUR


def capacity_by_hour(values_by_hour: dict[int, float], default: float = 0.0) -> np.ndarray:
    """288 values from one value per hour, e.g. ``{6: 300, 7: 500}``.
    Hours not in the dictionary take ``default``."""
    hourly_values = [values_by_hour.get(h, default) for h in range(24)]
    return np.repeat(hourly_values, SLOTS_PER_HOUR).astype(float)


def _period_slots(period: str) -> tuple[int, int]:
    try:
        start, end = (part.strip() for part in period.split("-"))
        start_min, end_min = _minutes(start), _minutes(end)
    except ValueError as error:
        raise ValueError(f"Period {period!r} must look like '06:00-12:00'") from error
    if not 0 <= start_min < end_min <= 24 * 60:
        raise ValueError(f"Period {period!r}: the start must be before the end, within the day")
    return start_min // SLOT_MINUTES, math.ceil(end_min / SLOT_MINUTES)


def _minutes(text: str) -> int:
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)
