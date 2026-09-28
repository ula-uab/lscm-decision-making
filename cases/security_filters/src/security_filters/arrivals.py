"""Presentation curve: passengers arriving at the security filters in each
5-minute slot of the day.

Slot ``s`` (0 to 287) covers the minutes ``[5s, 5s + 5)`` after midnight.
A flight that departs in slot ``d`` with ``P`` passengers adds
``P * f[i]`` passengers to slot ``d - i``, where ``f[i]`` is the fraction of
interval ``i`` of its arrival profile (interval 1 is the 5 minutes just
before departure).

Differences from the original macro (see ``legacy.py`` and the README):

- every interval of the profile is used, so each flight brings all its
  passengers (the macro ignored the last interval);
- passengers are not rounded flight by flight, so nothing is lost to rounding
  (the curve holds expected values, not whole passengers);
- flights that depart just after midnight are not ignored: their passengers
  that arrive after 00:00 are counted;
- passengers of early flights of the next day who arrive before midnight are
  counted (use ``schedule.flights_for_curve``);
- a shift that moves a flight outside the day does not stop the calculation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .schedule import SLOT_MINUTES, SLOTS_PER_DAY


def slot_labels() -> pd.Index:
    """Start time "HH:MM" of each of the 288 slots of the day."""
    minutes = np.arange(SLOTS_PER_DAY) * SLOT_MINUTES
    return pd.Index([f"{m // 60:02d}:{m % 60:02d}" for m in minutes], name="time")


def presentation_curve(flights: pd.DataFrame, profiles: pd.DataFrame,
                       profile: str = "erlang", load_factor: float = 1.0,
                       shift_slots: int = 0) -> pd.Series:
    """Passengers arriving at the filters in each slot of the day.

    ``flights`` needs the columns ``seats`` and ``departure_minute``. Three
    optional columns override the arguments flight by flight: ``profile``,
    ``load_factor`` and ``shift_slots`` (positive values move the arrivals of
    the flight later). An optional column ``day_offset`` (1 for flights of the
    next day) is added by ``schedule.flights_for_curve``.
    """
    curve = np.zeros(SLOTS_PER_DAY)
    n_intervals = len(profiles)
    offsets = np.arange(1, n_intervals + 1)

    for flight in flights.itertuples(index=False):
        name = _value(flight, "profile", profile)
        factor = _value(flight, "load_factor", load_factor)
        shift = int(_value(flight, "shift_slots", shift_slots))
        day_offset = int(_value(flight, "day_offset", 0))

        passengers = flight.seats * factor
        departure_slot = (flight.departure_minute // SLOT_MINUTES
                          + shift + day_offset * SLOTS_PER_DAY)
        slots = departure_slot - offsets
        inside = (slots >= 0) & (slots < SLOTS_PER_DAY)
        curve[slots[inside]] += passengers * profiles[name].to_numpy()[inside]

    return pd.Series(curve, index=slot_labels(), name="arrivals")


def _value(flight, column, default):
    """Value of an optional per-flight column, or the default if it is missing
    or empty for this flight."""
    value = getattr(flight, column, None)
    return default if value is None or pd.isna(value) else value


def hourly(curve: pd.Series) -> pd.Series:
    """Add up a 5-minute curve by hour of the day."""
    hours = np.arange(len(curve)) * SLOT_MINUTES // 60
    result = curve.groupby(hours).sum()
    result.index = pd.Index([f"{h:02d}:00" for h in result.index], name="hour")
    return result
