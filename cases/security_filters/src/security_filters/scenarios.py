"""Scenarios: what-if analysis of the filters on one day.

A scenario fixes how many passengers each flight brings (load factor), how
they arrive (arrival profile and shift) and how many passengers the filters
can serve in each 5-minute slot (capacity). Running it gives the presentation
curve, the queue and the indicators, so that several scenarios can be
compared on the same flights.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .arrivals import presentation_curve
from .indicators import simulate_queue, summary
from .schedule import SLOT_MINUTES, SLOTS_PER_DAY


@dataclass
class Scenario:
    """One set of assumptions.

    ``capacity`` is the number of passengers the filters can serve in each
    5-minute slot: one number for the whole day or 288 numbers, one per
    slot. The helpers ``capacity_from_fraction``, ``capacity_from_lanes``
    and ``capacity_by_hour`` build it.
    """
    name: str
    capacity: float | list[float] | np.ndarray
    profile: str = "erlang"
    load_factor: float = 1.0
    shift_slots: int = 0
    notes: str = field(default="", repr=False)


def run(scenario: Scenario, flights: pd.DataFrame, profiles: pd.DataFrame) -> pd.DataFrame:
    """Presentation curve, queue and idle time of a scenario (one row per slot)."""
    arrivals = presentation_curve(flights, profiles, profile=scenario.profile,
                                  load_factor=scenario.load_factor,
                                  shift_slots=scenario.shift_slots)
    capacity = np.broadcast_to(np.asarray(scenario.capacity, dtype=float),
                               (SLOTS_PER_DAY,))
    return simulate_queue(arrivals.to_numpy(), capacity)


def compare(scenarios: list[Scenario], flights: pd.DataFrame,
            profiles: pd.DataFrame) -> pd.DataFrame:
    """Indicators of several scenarios, one column per scenario."""
    return pd.DataFrame({s.name: summary(run(s, flights, profiles)) for s in scenarios})


def capacity_from_fraction(fraction, max_capacity: float = 500) -> np.ndarray:
    """Capacity as a fraction of the maximum, as in the original workbook
    (sheet "Hipotesis": fraction x 500 passengers per slot)."""
    return np.asarray(fraction, dtype=float) * max_capacity


def capacity_from_lanes(open_lanes, passengers_per_lane_per_hour: float) -> np.ndarray:
    """Capacity from the number of open lanes in each slot."""
    per_slot = passengers_per_lane_per_hour * SLOT_MINUTES / 60
    return np.asarray(open_lanes, dtype=float) * per_slot


def capacity_by_hour(values_by_hour: dict[int, float], default: float = 0.0) -> np.ndarray:
    """288 values from one value per hour, e.g. ``{6: 300, 7: 500}``.

    Hours not in the dictionary take ``default``.
    """
    slots_per_hour = 60 // SLOT_MINUTES
    hourly_values = [values_by_hour.get(h, default) for h in range(24)]
    return np.repeat(hourly_values, slots_per_hour).astype(float)
