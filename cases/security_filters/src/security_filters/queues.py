"""Queue at security screening when a capacity plan meets the real PPP (phase 6).

For each slot t of the day, a_t passengers arrive and the plan gives a
capacity c_t (open lanes times the capacity of a lane):

- the queue starts empty at 00:00;
- s_t = min(q_{t-1} + a_t, c_t) passengers go through security screening;
- q_t = q_{t-1} + a_t - s_t wait in the queue at the end of the slot;
- u_t = c_t - s_t is the unused capacity.

Passengers go through in order of arrival. The wait of a passenger is the
number of slots between the slot in which he or she arrives and the slot in
which he or she goes through, times 5 minutes (0 if both are the same slot),
so it is measured with an error of less than 5 minutes. If a queue is left at
24:00, its passengers go through after midnight with the capacity of the last
period, and their wait counts as well.

The case is not a problem of optimal queue management: the plan is not
optimised and the queue is not modelled in more detail.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .ppp import slot_labels
from .schedule import SLOT_MINUTES, SLOTS_PER_DAY


@dataclass
class QueueResult:
    """Queue of a day. ``slots`` has one row per slot of the day and, if a
    queue is left at 24:00, the slots after midnight until it is empty, with
    the columns ``arrivals``, ``capacity``, ``served``, ``unused`` and
    ``queue`` (at the end of the slot)."""
    slots: pd.DataFrame
    longest_wait_min: int
    longest_wait_arrival_slot: int | None

    @property
    def day(self) -> pd.DataFrame:
        """The 288 slots of the day, indexed by their start time."""
        return self.slots.iloc[:SLOTS_PER_DAY].set_index(slot_labels())

    @property
    def passengers(self) -> int:
        return int(self.slots["arrivals"].sum())

    @property
    def mean_wait_min(self) -> float:
        """Each passenger still in the queue at the end of a slot waits one
        slot more, so the sum of the queues is the sum of the waits."""
        return SLOT_MINUTES * self.slots["queue"].sum() / self.passengers if self.passengers else 0.0

    @property
    def highest_queue(self) -> int:
        return int(self.day["queue"].max())

    @property
    def highest_queue_slot(self) -> int:
        return int(self.day["queue"].to_numpy().argmax())

    @property
    def unused_capacity(self) -> int:
        """Unused capacity of the 288 slots of the day."""
        return int(self.day["unused"].sum())

    @property
    def queue_at_midnight(self) -> int:
        return int(self.day["queue"].iloc[-1])

    @property
    def cleared_after_midnight_min(self) -> int:
        """Minutes after 24:00 at which the queue is empty (0 if it is
        empty at 24:00)."""
        return (len(self.slots) - SLOTS_PER_DAY) * SLOT_MINUTES

    def hourly(self) -> pd.DataFrame:
        """Arrivals, capacity, passengers who go through and unused capacity
        of each hour, and the queue at the end of the hour."""
        day = self.day.reset_index(drop=True)
        by_hour = day.groupby(np.arange(len(day)) * SLOT_MINUTES // 60).agg(
            arrivals=("arrivals", "sum"), capacity=("capacity", "sum"),
            served=("served", "sum"), unused=("unused", "sum"), queue=("queue", "last"))
        by_hour.index = [f"{h:02d}:00–{h + 1:02d}:00" for h in by_hour.index]
        return by_hour


def apply_plan(arrivals, capacity) -> QueueResult:
    """Queue of a day with ``arrivals`` and ``capacity`` (288 values each,
    in passengers per slot)."""
    arrivals = [int(a) for a in np.asarray(arrivals)]
    capacity = [int(c) for c in np.asarray(capacity)]
    if len(arrivals) != len(capacity):
        raise ValueError("Arrivals and capacity need the same number of slots.")
    if capacity[-1] <= 0 and sum(arrivals) > 0:
        raise ValueError("The capacity of the last period must be greater than 0.")
    rows, waiting, t = [], 0, 0
    while t < len(arrivals) or waiting > 0:
        arriving = arrivals[t] if t < len(arrivals) else 0
        cap = capacity[t] if t < len(capacity) else capacity[-1]
        served = min(waiting + arriving, cap)
        waiting = waiting + arriving - served
        rows.append((arriving, cap, served, cap - served, waiting))
        t += 1
    slots = pd.DataFrame(rows, columns=["arrivals", "capacity", "served", "unused", "queue"])

    # Longest wait: the passengers who arrive in slot t finish going through
    # in the first slot t' with D_t' >= A_t
    arrived = slots["arrivals"].cumsum().to_numpy()
    departed = slots["served"].cumsum().to_numpy()
    longest, longest_slot = 0, None
    for t, arriving in enumerate(arrivals):
        if arriving > 0:
            done = int(np.argmax(departed >= arrived[t]))
            if longest_slot is None or done - t > longest:
                longest, longest_slot = done - t, t
    return QueueResult(slots, longest * SLOT_MINUTES, longest_slot)
