"""PPP of the airport: passengers who arrive at the security checkpoint in each slot.

The calculations follow §6 of the design of the case:

- passengers of a flight who go through security screening (Equations E.7 to E.9):
  ``B = round(L A)``, ``R = round(T B)``, ``Q = B - R``;
- whole passengers in each slot of the flight (Equation E.11): the
  cumulative number of passengers up to each slot is rounded, and the
  passengers of a slot are the difference between two consecutive rounded
  cumulative numbers, so the slots of a flight add up to ``Q`` and none is
  negative;
- slot ``k`` of a flight is slot ``d - g - k - c`` of the day (Equations
  E.5 and E.10), where ``d`` is the slot of its STD, ``g`` the slots between
  the closing of the gate and the STD and ``c`` its surge offset. For a
  flight of the next day, ``d`` is its slot plus 288.

Round gives the nearest whole number, and 0.5 is rounded up. Passengers who
would arrive before 00:00 or after 24:00 are not in the PPP of the day; they
are counted apart, so that no passenger is lost.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .schedule import SLOT_MINUTES, SLOTS_PER_DAY

N_SLOTS = 29     # slots of the PPP of a flight (n)
GATE_SLOTS = 6   # slots between the closing of the gate and the STD (g), 30 minutes

# Products such as 0.25 * 98 = 24.5 may come out of the floating-point
# arithmetic as 24.499999999999996: the tolerance keeps them at .5
_TOLERANCE = 1e-9


def round_half_up(x) -> np.ndarray:
    """Nearest whole number, with 0.5 rounded up."""
    return np.floor(np.asarray(x, dtype=float) + 0.5 + _TOLERANCE)


def flight_passengers(seats, load_factor, transit_share) -> tuple:
    """Passengers who fly ``B``, in transit ``R`` and through security screening
    ``Q`` (Equations E.7 to E.9). Arguments can be numbers or arrays."""
    boarding = round_half_up(np.asarray(load_factor, dtype=float) * np.asarray(seats, dtype=float))
    transit = round_half_up(np.asarray(transit_share, dtype=float) * boarding)
    return boarding.astype(int), transit.astype(int), (boarding - transit).astype(int)


def whole_passengers(passengers: int, shares: np.ndarray) -> np.ndarray:
    """Whole passengers of a flight in each slot ``1, ..., n`` of its
    pattern (Equation E.11)."""
    cumulative = round_half_up(passengers * np.cumsum(shares))
    cumulative[-1] = passengers  # the shares add up to 1 up to rounding errors
    return np.diff(np.concatenate([[0.0], cumulative])).astype(int)


def slot_labels() -> pd.Index:
    """Start time "HH:MM" of each of the 288 slots of the day."""
    minutes = np.arange(SLOTS_PER_DAY) * SLOT_MINUTES
    return pd.Index([f"{m // 60:02d}:{m % 60:02d}" for m in minutes], name="time")


def hourly(curve: pd.Series) -> pd.Series:
    """Add up a 5-minute curve by hour of the day."""
    hours = np.arange(len(curve)) * SLOT_MINUTES // 60
    result = curve.groupby(hours).sum()
    result.index = pd.Index([f"{h:02d}:00" for h in result.index], name="hour")
    return result


@dataclass
class PPP:
    """PPP of the airport for some flights.

    ``arrivals``: passengers in each slot of the day (288 values, indexed by
    the start time of the slot). ``before_midnight`` and ``after_midnight``:
    passengers of these flights who arrive outside the day. ``passengers``:
    the sum of ``Q`` of the flights, which is always the sum of the three.
    ``flights``: the flights with their ``boarding``, ``transit`` and
    ``passengers`` (``B``, ``R`` and ``Q``).
    """
    arrivals: pd.Series
    before_midnight: int
    after_midnight: int
    passengers: int
    flights: pd.DataFrame

    @property
    def peak_slot(self) -> int:
        """Slot of the day with most passengers (the first one, if several)."""
        return int(self.arrivals.to_numpy().argmax())


def airport_ppp(flights: pd.DataFrame, n: int = N_SLOTS, gate: int = GATE_SLOTS) -> PPP:
    """PPP of the airport for ``flights``: the flights of a scenario
    (``Scenario.flights``), or some of them.

    ``flights`` needs the columns ``seats``, ``load_factor``,
    ``transit_share``, ``pattern``, ``offset``, ``departure_minute`` and
    ``day_offset`` (1 for the flights of the next day).
    """
    boarding, transit, passengers = flight_passengers(
        flights["seats"], flights["load_factor"], flights["transit_share"])
    arrivals = np.zeros(SLOTS_PER_DAY, dtype=int)
    before = after = 0
    shares = {}
    departure_slot = (flights["departure_minute"].to_numpy() // SLOT_MINUTES
                      + SLOTS_PER_DAY * flights["day_offset"].to_numpy())
    for pattern, q, d, c in zip(flights["pattern"], passengers, departure_slot,
                                flights["offset"].to_numpy()):
        if pattern not in shares:
            shares[pattern] = pattern.shares(n)
        per_slot = whole_passengers(int(q), shares[pattern])
        day_slot = d - gate - np.arange(1, n + 1) - c
        inside = (day_slot >= 0) & (day_slot < SLOTS_PER_DAY)
        np.add.at(arrivals, day_slot[inside], per_slot[inside])
        before += int(per_slot[day_slot < 0].sum())
        after += int(per_slot[day_slot >= SLOTS_PER_DAY].sum())
    table = flights.assign(boarding=boarding, transit=transit, passengers=passengers)
    return PPP(pd.Series(arrivals, index=slot_labels(), name="passengers"), before, after,
               int(passengers.sum()), table)
