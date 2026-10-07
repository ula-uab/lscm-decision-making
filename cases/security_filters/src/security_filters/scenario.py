"""A demand scenario: the values of the flights of one day.

The student does not set the values flight by flight. He or she selects a
group of flights with the filters (airlines and destinations) and gives the
group some values: load factor, share of passengers in transit and arrival
pattern. The flights of an arrival surge are chosen one by one, among the
flights of one airline. Every flight starts with the same default values.

A scenario keeps the list of these **steps**, in the order in which they
were made. The values of the flights are the result of applying the steps
in that order: when two steps select the same flight, the flight keeps the
values of the last one. The steps can be saved to a JSON file and loaded
again, and they give the same values.

The flights of a scenario are those of the day under study and the flights
of the next day that depart before 02:55, because some of their passengers
arrive before midnight.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pandas as pd

from .patterns import DEFAULT_PATTERN, ArrivalPattern
from .ppp import N_SLOTS
from .schedule import SLOT_MINUTES, flights_for_curve, read_schedule

# Next-day flights before 02:55: n = 29 slots of a pattern plus g = 6 slots
# (lecturer, 05/10/2026)
NEXT_DAY_SLOTS = 35
FORMAT_VERSION = 1

DEFAULTS = {"load_factor": 1.0, "transit_share": 0.0, "pattern": DEFAULT_PATTERN}
VALUES = tuple(DEFAULTS)


def flights_of_scenario(schedule: pd.DataFrame, day: str) -> pd.DataFrame:
    """Flights of ``day`` and next-day flights before 02:55, indexed by
    ``flight_id``. The column ``minute`` counts the minutes of departure from
    midnight of ``day`` (next-day flights add 24 hours)."""
    flights = flights_for_curve(schedule, day, max_slots_before=NEXT_DAY_SLOTS)
    flights["minute"] = flights["departure_minute"] + 24 * 60 * flights["day_offset"]
    return flights.set_index("flight_id")


def select(flights: pd.DataFrame, airlines=(), destinations=()) -> pd.Series:
    """Flights of the given airlines and destinations (ICAO and IATA codes).
    An empty list does not filter."""
    match = pd.Series(True, index=flights.index)
    if airlines:
        match &= flights["airline"].isin(list(airlines))
    if destinations:
        match &= flights["destination"].isin(list(destinations))
    return match


class Scenario:
    """The values of the flights of one day, built step by step."""

    def __init__(self, day: str, name: str = "", schedule: pd.DataFrame | None = None,
                 steps: list[dict] | None = None):
        self.day = str(day)
        self.name = name
        self._schedule = read_schedule() if schedule is None else schedule
        self._base = flights_of_scenario(self._schedule, self.day)
        if self._base.empty:
            raise ValueError(f"There are no flights on {self.day}")
        self.steps: list[dict] = []
        self._reset()
        for step in copy.deepcopy(steps or []):
            self._apply(step)
            self.steps.append(step)

    # ---------- steps ----------
    def assign(self, airlines=(), destinations=(), load_factor: float | None = None,
               transit_share: float | None = None,
               pattern: ArrivalPattern | None = None) -> int:
        """Give values to the flights of the airlines and destinations.
        Only the values that are given change. Returns the number of flights."""
        values = {}
        if load_factor is not None:
            values["load_factor"] = _share(load_factor, "The load factor")
        if transit_share is not None:
            values["transit_share"] = _share(transit_share, "The share of passengers in transit")
        if pattern is not None:
            values["pattern"] = pattern.to_dict()
        if not values:
            raise ValueError("Choose at least one value to give to the flights.")
        step = {"action": "assign", "airlines": sorted(airlines),
                "destinations": sorted(destinations), "values": values}
        return self._record(step)

    def surge(self, flight_ids) -> str:
        """Make an arrival surge with the given flights (``flight_id``) of
        one airline. Returns the name of the surge."""
        members = list(dict.fromkeys(flight_ids))
        unknown = [f for f in members if f not in self._base.index]
        if unknown:
            raise ValueError(f"These flights are not in the scenario: {', '.join(unknown)}")
        if len(members) < 2:
            raise ValueError("An arrival surge needs at least two flights.")
        airlines = self._base.loc[members, "airline"].unique()
        if len(airlines) > 1:
            raise ValueError("An arrival surge must have flights of one airline only. "
                             f"The selection has flights of: {', '.join(sorted(airlines))}.")
        return self._record({"action": "surge", "flights": members})

    def remove_surge(self, name: str) -> None:
        """Remove an arrival surge: its flights go back to offset 0."""
        if name not in self._surges:
            raise ValueError(f"There is no arrival surge called {name!r}.")
        self._record({"action": "remove surge", "surge": name})

    # ---------- results ----------
    @property
    def flights(self) -> pd.DataFrame:
        """Flights with their values: ``load_factor``, ``transit_share``,
        ``pattern`` (an ``ArrivalPattern``), ``surge`` (its name, or empty)
        and ``offset`` (5-minute slots from the reference flight of its
        surge; 0 without surge)."""
        return self._flights.copy()

    def surges(self) -> pd.DataFrame:
        """One row per arrival surge: airline, flights, first and last
        departure, and offsets of its flights in order of departure."""
        rows = []
        for name, members in self._surges.items():
            group = self._flights.loc[members].sort_values("minute")
            rows.append({"surge": name, "airline": group["airline"].iloc[0],
                         "flights": len(group), "from": group["departure"].iloc[0],
                         "to": group["departure"].iloc[-1],
                         "reference": group["flight"].iloc[0],
                         "offsets": list(group["offset"])})
        columns = ["surge", "airline", "flights", "from", "to", "reference", "offsets"]
        return pd.DataFrame(rows, columns=columns).set_index("surge")

    # ---------- files ----------
    def to_dict(self) -> dict:
        """The scenario as it is now: later steps do not change the result."""
        return {"format_version": FORMAT_VERSION, "name": self.name, "day": self.day,
                "steps": copy.deepcopy(self.steps)}

    @classmethod
    def from_dict(cls, data: dict, schedule: pd.DataFrame | None = None) -> "Scenario":
        try:
            return cls(data["day"], data.get("name", ""), schedule, data["steps"])
        except (KeyError, TypeError) as error:
            raise ValueError("This is not a scenario file.") from error

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path, schedule: pd.DataFrame | None = None) -> "Scenario":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")), schedule)

    # ---------- internals ----------
    def _reset(self) -> None:
        self._flights = self._base.copy()
        for column, value in DEFAULTS.items():
            self._flights[column] = [value] * len(self._flights)
        self._surges: dict[str, list[str]] = {}
        self._next_surge = 1
        self._update_offsets()

    def _record(self, step: dict):
        result = self._apply(step)
        self.steps.append(step)
        return result

    def _apply(self, step: dict):
        action = step.get("action")
        if action == "assign":
            match = select(self._flights, step["airlines"], step["destinations"])
            if not match.any():
                raise ValueError("No flight matches the selection.")
            # All the values are checked before any flight changes
            values = {}
            for column, value in step["values"].items():
                if column == "pattern":
                    value = ArrivalPattern.from_dict(value)
                    value.shares(N_SLOTS)  # raises if the pattern gives no passengers
                if column not in VALUES:
                    raise ValueError(f"Unknown value {column!r}")
                values[column] = value
            for column, value in values.items():
                self._flights.loc[match, column] = pd.Series([value] * match.sum(),
                                                             index=match[match].index)
            return int(match.sum())
        if action == "surge":
            members = step["flights"]
            for name in list(self._surges):  # a flight is in one surge only
                left = [f for f in self._surges[name] if f not in members]
                if len(left) >= 2:
                    self._surges[name] = left
                else:
                    del self._surges[name]
            name = f"Surge {self._next_surge}"
            self._next_surge += 1
            self._surges[name] = list(members)
            self._update_offsets()
            return name
        if action == "remove surge":
            del self._surges[step["surge"]]
            self._update_offsets()
            return None
        raise ValueError(f"Unknown step {action!r}")

    def _update_offsets(self) -> None:
        self._flights["surge"] = ""
        self._flights["offset"] = 0
        for name, members in self._surges.items():
            minute = self._flights.loc[members, "minute"]
            self._flights.loc[members, "surge"] = name
            self._flights.loc[members, "offset"] = (minute - minute.min()) // SLOT_MINUTES


def _share(value: float, what: str) -> float:
    value = float(value)
    if not 0 <= value <= 1:
        raise ValueError(f"{what} must be between 0 and 1.")
    return value
