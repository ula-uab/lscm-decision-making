"""Queue at the filters and performance indicators.

In each 5-minute slot the filters can serve up to ``capacity`` passengers.
Passengers who cannot be served wait for the next slot:

    served[t] = min(capacity[t], queue[t-1] + arrivals[t])
    queue[t]  = queue[t-1] + arrivals[t] - served[t]
    idle[t]   = (capacity[t] - served[t]) / capacity[t]

The queue is counted at the end of each slot and starts empty at 00:00.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .arrivals import slot_labels
from .schedule import SLOT_MINUTES


def simulate_queue(arrivals, capacity) -> pd.DataFrame:
    """Served passengers, queue and idle fraction of the filters in each slot."""
    arrivals = np.asarray(arrivals, dtype=float)
    capacity = np.broadcast_to(np.asarray(capacity, dtype=float), arrivals.shape)
    served = np.zeros_like(arrivals)
    queue = np.zeros_like(arrivals)
    waiting = 0.0
    for t in range(len(arrivals)):
        served[t] = min(capacity[t], waiting + arrivals[t])
        waiting = waiting + arrivals[t] - served[t]
        queue[t] = waiting
    with np.errstate(divide="ignore", invalid="ignore"):
        idle = np.where(capacity > 0, (capacity - served) / capacity, 0.0)
    return pd.DataFrame({"arrivals": arrivals, "capacity": capacity,
                         "served": served, "queue": queue, "idle": idle},
                        index=slot_labels()[:len(arrivals)])


def summary(result: pd.DataFrame) -> pd.Series:
    """Indicators of a day, from the table of ``simulate_queue``.

    - ``average_wait_min``: average wait per passenger, with Little's law
      (average queue divided by the arrival rate);
    - ``max_wait_min``: the longest estimated wait: minutes needed to clear
      the queue at the end of a slot with the capacity of the next slot;
    - ``waiting_pax_min``: total passenger-minutes spent in the queue.
    """
    total = result["arrivals"].sum()
    minutes = len(result) * SLOT_MINUTES
    queue = result["queue"].to_numpy()
    next_capacity = np.append(result["capacity"].to_numpy()[1:], result["capacity"].iloc[-1])
    with np.errstate(divide="ignore", invalid="ignore"):
        clearing = np.where(queue > 0, queue / next_capacity * SLOT_MINUTES, 0.0)
    peak = result["queue"].idxmax()
    average_wait = (result["queue"].mean() / (total / minutes)) if total > 0 else 0.0
    return pd.Series({
        "passengers": total,
        "max_queue": queue.max(),
        "time_of_max_queue": peak if queue.max() > 0 else "-",
        "slots_with_queue": int((queue > 0.5).sum()),
        "queue_at_midnight": queue[-1],
        "average_wait_min": average_wait,
        "max_wait_min": clearing.max(),
        "waiting_pax_min": queue.sum() * SLOT_MINUTES,
        "capacity_used": result["served"].sum() / result["capacity"].sum(),
        "average_idle": result["idle"].mean(),
    })
