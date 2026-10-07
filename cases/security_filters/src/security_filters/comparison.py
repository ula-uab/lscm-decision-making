"""Comparison of the PPPs of several scenarios of the same day.

The comparison only puts the PPPs and their summaries side by side, in the
order in which the scenarios are given. It does not compute differences,
mark where the PPPs cross, or rank the scenarios: analysing them is the
student's work.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .ppp import PPP, airport_ppp
from .scenario import Scenario
from .schedule import SLOT_MINUTES

SLOTS_PER_HOUR = 60 // SLOT_MINUTES


def summary(result: PPP) -> pd.Series:
    """Summary of a PPP, the same data as section 2 of the notebook:
    passengers in the day and outside it, highest value and its slot,
    busiest hour and its passengers."""
    curve = result.arrivals
    peak = result.peak_slot
    end = (peak + 1) * SLOT_MINUTES
    by_hour = hours(curve)
    busiest = int(by_hour.to_numpy().argmax())
    return pd.Series({
        "Passengers in the day": int(curve.sum()),
        "Arrive before 00:00": result.before_midnight,
        "Arrive after 24:00": result.after_midnight,
        "All the flights": result.passengers,
        "Highest value": int(curve.iloc[peak]),
        "Slot of the highest value": f"{curve.index[peak]}–{end // 60:02d}:{end % 60:02d}",
        "Busiest hour": by_hour.index[busiest],
        "Passengers in the busiest hour": int(by_hour.iloc[busiest]),
    }, dtype=object)


def hours(curve):
    """Passengers of each hour of the day, indexed "HH:00–HH:00"."""
    by_hour = curve.groupby(np.arange(len(curve)) // SLOTS_PER_HOUR).sum()
    by_hour.index = [f"{h:02d}:00–{h + 1:02d}:00" for h in range(len(by_hour))]
    return by_hour


@dataclass
class Comparison:
    """PPPs of several scenarios of one day, in the order given."""
    day: str
    results: dict[str, PPP]

    @property
    def curves(self) -> pd.DataFrame:
        """Passengers in each of the 288 slots: one column per scenario."""
        return pd.DataFrame({name: r.arrivals for name, r in self.results.items()})

    @property
    def summary(self) -> pd.DataFrame:
        """Summary of each scenario, one column per scenario."""
        return pd.DataFrame({name: summary(r) for name, r in self.results.items()})

    @property
    def hourly(self) -> pd.DataFrame:
        """Passengers of each hour, one column per scenario."""
        return hours(self.curves)


def compare(scenarios: dict[str, Scenario]) -> Comparison:
    """PPPs of ``scenarios`` (by name, in the order given), which must be
    of the same day."""
    if not scenarios:
        raise ValueError("Choose the scenarios to compare.")
    days: dict[str, list[str]] = {}
    for name, scenario in scenarios.items():
        days.setdefault(scenario.day, []).append(name)
    if len(days) > 1:
        listed = " and ".join(f"{day} ({', '.join(names)})" for day, names in days.items())
        raise ValueError(f"The scenarios must be of the same day. The selection has {listed}.")
    results = {name: airport_ppp(scenario.flights) for name, scenario in scenarios.items()}
    return Comparison(next(iter(days)), results)
