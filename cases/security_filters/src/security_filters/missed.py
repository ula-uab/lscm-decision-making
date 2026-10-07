"""Passengers who go through the filters after the closing of the gate of
their flight, with a capacity plan applied to a demand (design, §7,
assumptions 14 to 16).

Each passenger arrives at the filters in a slot of the day, and the gate of
his or her flight closes at the end of a later slot: ``k`` is the number of
slots from the slot of arrival to that slot, counting both (``k = 1`` when
the gate closes at the end of the slot of arrival). The queue is served in
order of arrival (``apply_plan``), so the passengers of a slot of arrival go
through in known numbers in that slot and the following ones. Within a slot
of arrival the passengers of different flights are mixed: each part that
goes through in a slot is shared out among them in proportion to the
passengers still waiting, in whole passengers (largest remainders), so the
same data always give the same figures.

A passenger misses the closing if he or she goes through after the slot
that ends when the gate closes, minus the walk from the filters to the gate.
With a walk of ``m`` slots, the passengers with ``k <= m`` would miss it
even with no queue: they are counted apart, and only the rest is due to the
queue. Nobody leaves the queue, and there is no priority lane.

With a scenario, the flights are known and the count is exact. The real PPP
comes without its flights: ``data/real_ppp_gate.csv`` gives, for each slot,
how many of its passengers have ``k`` from 1 to 12 (up to 60 minutes) and
how many more. Passengers with ``k`` above 12 who wait long enough could
also miss the closing; then the count is a lower bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import numpy as np
import pandas as pd

from .ppp import GATE_SLOTS, N_SLOTS, flight_passengers, whole_passengers
from .queues import QueueResult
from .schedule import SLOT_MINUTES, SLOTS_PER_DAY

HORIZON = 12             # slots of the real data on the closing of the gate (60 minutes)
MORE = "more"            # column of the passengers whose gate closes later than that
WALKS_MIN = (0, 5, 10, 15, 20, 25, 30)


@dataclass
class MissedResult:
    """Passengers who miss the closing of their gate.

    ``by_queue``: those who miss it because of the queue. ``anyway``: those
    who would miss it even with no queue (only with a walk above 0).
    ``complete``: False when the count is a lower bound. ``flights``: with a
    scenario, one row per flight with passengers who miss the closing
    because of the queue; ``None`` with the real PPP. ``by_hour``: the
    passengers who miss it because of the queue, by hour of departure.
    """
    walk_min: int
    by_queue: int
    anyway: int
    complete: bool
    flights: pd.DataFrame | None
    by_hour: pd.Series


def _share(waiting: np.ndarray, n: int) -> np.ndarray:
    """``n`` whole passengers shared out in proportion to ``waiting``, with
    the largest remainders (ties to the first group)."""
    total = int(waiting.sum())
    numerators = waiting * n
    parts = numerators // total
    left = n - int(parts.sum())
    if left:
        order = np.argsort(-(numerators % total), kind="stable")[:left]
        parts[order] += 1
    return parts


def _going_through(queue: QueueResult) -> dict[int, dict[int, int]]:
    """For each slot of arrival, the passengers of that slot who go through
    in each slot (first come, first served)."""
    arrived = queue.slots["arrivals"].cumsum().to_numpy()
    served = queue.slots["served"].cumsum().to_numpy()
    blocks = {}
    for t in range(SLOTS_PER_DAY):
        low, high = (int(arrived[t - 1]) if t else 0), int(arrived[t])
        blocks[t] = {}
        if high == low:
            continue
        u = int(np.searchsorted(served, low, side="right"))
        while True:
            part = min(high, int(served[u])) - max(low, int(served[u - 1]) if u else 0)
            if part > 0:
                blocks[t][u] = part
            if served[u] >= high:
                break
            u += 1
    return blocks


def count_missed(queue: QueueResult, groups: pd.DataFrame, walk_min: int) -> tuple:
    """``groups``: one row per group of passengers of a slot of arrival, with
    ``slot``, ``k`` (0 when it is only known to be above ``HORIZON``),
    ``passengers`` and ``key``. Returns the passengers who miss the closing
    because of the queue by key, those who miss it anyway, and whether the
    count is complete."""
    walk = walk_min // SLOT_MINUTES
    blocks = _going_through(queue)
    by_key: dict = {}
    anyway, complete = 0, True
    for t, of_slot in groups.groupby("slot", sort=True):
        k = of_slot["k"].to_numpy()
        waiting = of_slot["passengers"].to_numpy().astype(np.int64)
        keys = of_slot["key"].to_numpy()
        known = k > 0
        without_queue = known & (k <= walk)
        anyway += int(waiting[without_queue].sum())
        for u, n in blocks[int(t)].items():
            parts = _share(waiting, n)
            waiting = waiting - parts
            late = known & ~without_queue & (u > t + k - 1 - walk)
            for key, part in zip(keys[late], parts[late]):
                if part:
                    by_key[key] = by_key.get(key, 0) + int(part)
            # Passengers with k above the horizon could miss the closing too
            if u - t >= HORIZON + 1 - walk and parts[~known].sum() > 0:
                complete = False
    return by_key, anyway, complete


def _hour(minute: int) -> str:
    hour = minute // 60
    return f"{hour % 24:02d}:00" + (" (+1)" if hour >= 24 else "")


def scenario_groups(flights: pd.DataFrame) -> pd.DataFrame:
    """Passengers of each flight by slot of arrival and ``k``, for the
    flights of a scenario (the columns of ``Scenario.flights``). Only the
    slots of the day."""
    passengers = flight_passengers(flights["seats"], flights["load_factor"],
                                   flights["transit_share"])[2]
    rows = []
    departure = (flights["departure_minute"].to_numpy() // SLOT_MINUTES
                 + SLOTS_PER_DAY * flights["day_offset"].to_numpy())
    for flight_id, pattern, q, d, c in zip(flights.index, flights["pattern"], passengers,
                                           departure, flights["offset"].to_numpy()):
        per_slot = whole_passengers(int(q), pattern.shares(N_SLOTS))
        for i, p in enumerate(per_slot, start=1):
            t = d - GATE_SLOTS - i - c
            if p and 0 <= t < SLOTS_PER_DAY:
                rows.append((int(t), int(i + c), int(p), flight_id))
    return pd.DataFrame(rows, columns=["slot", "k", "passengers", "key"])


def gate_table(flights: pd.DataFrame) -> pd.DataFrame:
    """Passengers of each slot of the day by ``k``, from 1 to ``HORIZON``,
    and those with ``k`` above it (column ``more``): the content of
    ``real_ppp_gate.csv`` for one day."""
    groups = scenario_groups(flights)
    column = groups["k"].where(groups["k"] <= HORIZON, MORE).astype(str)
    table = (groups.assign(column=column).groupby(["slot", "column"])["passengers"].sum()
             .unstack(fill_value=0)
             .reindex(index=range(SLOTS_PER_DAY), columns=[str(k) for k in range(1, HORIZON + 1)]
                      + [MORE], fill_value=0))
    return table.astype(int)


def read_real_gate(day: str, path: str | Path | None = None) -> pd.DataFrame:
    """The table of ``gate_table`` for the real PPP of ``day``: 288 rows."""
    if path is None:
        path = Path(str(resources.files("security_filters") / "data" / "real_ppp_gate.csv"))
    table = pd.read_csv(path, dtype={"day": str})
    of_day = table[table["day"] == str(day)]
    if of_day.empty:
        raise ValueError(f"There are no real data on the closing of the gates for {day}.")
    return of_day.drop(columns=["day", "slot start"]).reset_index(drop=True)


def missed_with_scenario(flights: pd.DataFrame, queue: QueueResult,
                         walk_min: int = 0) -> MissedResult:
    """Passengers of the flights of a scenario who miss the closing of their
    gate, with ``queue`` (the plan applied to the PPP of that scenario)."""
    groups = scenario_groups(flights)
    by_flight, anyway, _ = count_missed(queue, groups, walk_min)
    passengers = pd.Series(flight_passengers(flights["seats"], flights["load_factor"],
                                             flights["transit_share"])[2], index=flights.index)
    hit = flights.loc[list(by_flight)].assign(
        passengers=passengers[list(by_flight)], missed=list(by_flight.values()))
    minute = hit["departure_minute"] + 24 * 60 * hit["day_offset"]
    table = pd.DataFrame({
        "Flight": hit["flight"], "Airline": hit["airline"], "Destination": hit["destination"],
        "STD": [f"{m // 60 % 24:02d}:{m % 60:02d}" + (" (+1)" if m >= 24 * 60 else "")
                for m in minute],
        "Passengers of the flight": hit["passengers"].astype(int),
        "Miss the closing": hit["missed"].astype(int),
    }).assign(_order=minute.to_numpy()).sort_values(["_order", "Flight"]).drop(columns="_order")
    by_hour = (pd.Series(list(by_flight.values()), index=[_hour(int(m)) for m in minute])
               .groupby(level=0, sort=False).sum()) if len(hit) else pd.Series(dtype=int)
    return MissedResult(walk_min, int(sum(by_flight.values())), anyway, True,
                        table.reset_index(drop=True), by_hour)


def missed_with_real(day: str, queue: QueueResult, walk_min: int = 0,
                     path: str | Path | None = None) -> MissedResult:
    """Passengers of the real PPP of ``day`` who miss the closing of their
    gate, with ``queue`` (the plan applied to the real PPP), by hour of
    departure. A lower bound when some waits are too long for the data."""
    table = read_real_gate(day, path)
    rows = []
    for t, row in table.iterrows():
        for column, p in row.items():
            if p:
                k = 0 if column == MORE else int(column)
                minute = (t + k) * SLOT_MINUTES + GATE_SLOTS * SLOT_MINUTES   # STD of the flight
                rows.append((int(t), k, int(p), _hour(minute) if k else MORE))
    groups = pd.DataFrame(rows, columns=["slot", "k", "passengers", "key"])
    by_hour, anyway, complete = count_missed(queue, groups, walk_min)
    order = sorted(by_hour, key=lambda h: (h.endswith("(+1)"), h))
    return MissedResult(walk_min, int(sum(by_hour.values())), anyway, complete, None,
                        pd.Series({h: by_hour[h] for h in order}, dtype=int))
