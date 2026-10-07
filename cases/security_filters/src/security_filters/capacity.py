"""Capacity plan of security screening (phase 5).

The airport sets the screening capacity before the day starts by
opening more or fewer lanes. Two parameters describe the screening lanes (lecturer,
06/10/2026):

- ``lanes_available``: the number of lanes, L (10 by default);
- ``lane_capacity``: the passengers that one lane serves in a 5-minute slot,
  C_L (50 by default), a whole number.

The maximum capacity is ``Cmax = L * C_L`` passengers per slot (500 by
default). A plan divides the day into periods that start on the hour; each
period keeps from 1 to L lanes open (0 is not allowed), so the capacity of
each of its slots is ``lanes * C_L``. The first period starts at 00:00 and
the last one ends at 24:00.

The plan does not compute queues or unused capacity (phase 6), and it does
not propose or judge a plan.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .ppp import slot_labels
from .schedule import SLOT_MINUTES, SLOTS_PER_DAY

LANES_AVAILABLE = 10
LANE_CAPACITY = 50
FORMAT_VERSION = 1
SLOTS_PER_HOUR = 60 // SLOT_MINUTES


@dataclass
class CapacityPlan:
    """Open lanes in each period of the day.

    ``periods`` is a list of ``{"start": "HH:00", "lanes": n}``; it is kept
    in order of start time.
    """
    periods: list[dict] = field(default_factory=lambda: [{"start": "00:00", "lanes": LANES_AVAILABLE}])
    lanes_available: int = LANES_AVAILABLE
    lane_capacity: int = LANE_CAPACITY
    name: str = ""

    def __post_init__(self):
        self.lanes_available = _whole(self.lanes_available, "The number of lanes available")
        self.lane_capacity = _whole(self.lane_capacity, "The capacity of a lane")
        periods = []
        for period in self.periods:
            start = str(period["start"])
            hour, _, minute = start.partition(":")
            if not (hour.isdigit() and minute == "00" and 0 <= int(hour) <= 23):
                raise ValueError(f"A period must start on the hour, from 00:00 to 23:00, not at {start}.")
            lanes = period["lanes"]
            if isinstance(lanes, bool) or not float(lanes).is_integer():
                raise ValueError(f"The period that starts at {start} needs a whole number of lanes.")
            if not 1 <= int(lanes) <= self.lanes_available:
                raise ValueError(f"The period that starts at {start} has {lanes} lanes; it needs "
                                 f"from 1 to {self.lanes_available}.")
            periods.append({"start": f"{int(hour):02d}:00", "lanes": int(lanes)})
        starts = [p["start"] for p in periods]
        repeated = sorted({s for s in starts if starts.count(s) > 1})
        if repeated:
            raise ValueError(f"Two periods start at {repeated[0]}. Each period needs its own "
                             "start time.")
        if "00:00" not in starts:
            raise ValueError("The first period must start at 00:00.")
        self.periods = sorted(periods, key=lambda p: p["start"])

    @property
    def max_capacity(self) -> int:
        """Cmax = L * C_L, passengers per 5-minute slot with every lane open."""
        return self.lanes_available * self.lane_capacity

    def capacity(self) -> pd.Series:
        """Capacity of each of the 288 slots of the day, in passengers."""
        result = np.zeros(SLOTS_PER_DAY, dtype=int)
        bounds = [int(p["start"][:2]) * SLOTS_PER_HOUR for p in self.periods] + [SLOTS_PER_DAY]
        for period, first, last in zip(self.periods, bounds, bounds[1:]):
            result[first:last] = period["lanes"] * self.lane_capacity
        return pd.Series(result, index=slot_labels(), name="capacity")

    def table(self) -> pd.DataFrame:
        """One row per period: start, end, open lanes, share of Cmax and
        capacity per slot."""
        ends = [p["start"] for p in self.periods[1:]] + ["24:00"]
        return pd.DataFrame({
            "From": [p["start"] for p in self.periods],
            "To": ends,
            "Open lanes": [p["lanes"] for p in self.periods],
            "% of Cmax": [f"{p['lanes'] / self.lanes_available:.0%}" for p in self.periods],
            "Capacity per slot": [p["lanes"] * self.lane_capacity for p in self.periods],
        }, index=pd.RangeIndex(1, len(self.periods) + 1, name="Period"))

    # ---------- files ----------
    def to_dict(self) -> dict:
        return {"format_version": FORMAT_VERSION, "name": self.name,
                "lanes_available": self.lanes_available, "lane_capacity": self.lane_capacity,
                "periods": copy.deepcopy(self.periods)}

    @classmethod
    def from_dict(cls, data: dict) -> "CapacityPlan":
        try:
            return cls(copy.deepcopy(data["periods"]), data["lanes_available"],
                       data["lane_capacity"], data.get("name", ""))
        except (KeyError, TypeError) as error:
            raise ValueError("This is not a capacity plan.") from error

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "CapacityPlan":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _whole(value, what: str) -> int:
    if isinstance(value, bool) or not float(value).is_integer() or value < 1:
        raise ValueError(f"{what} must be a whole number greater than 0.")
    return int(value)
