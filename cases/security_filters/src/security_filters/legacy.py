"""Faithful reproduction of the original Excel workbooks, errors included.

It is used to check that this package reads the data and understands the
method in the same way as the original case, and to measure what changes
when the errors are corrected. It is not meant for analysis: use
``arrivals.presentation_curve`` and ``indicators.simulate_queue`` instead.

- ``legacy_presentation_curve`` reproduces the macro ``calcula_pax_franja``
  and the function ``aplicarDistribucion`` of
  ``ProcesaDatosVuelos-plantilla-original.xls`` (module ``processFlights``).
- ``legacy_performance`` reproduces the sheet "Rendimientos" of
  ``indicadores-filtros-parte2.xls``.
"""

from __future__ import annotations

import pandas as pd

from .arrivals import slot_labels
from .schedule import SLOT_MINUTES, SLOTS_PER_DAY


def legacy_presentation_curve(flights: pd.DataFrame, profiles: pd.DataFrame,
                              profile: str = "erlang", load_factor: float = 1.0,
                              oleada: int = 0) -> pd.Series:
    """Curve computed as the macro does, including its errors.

    ``flights`` are the flights of one day (``schedule.flights_of_day``).
    ``oleada`` is the "CorrecionFranja" of the sheet "Paso2", in slots, with
    the sign of the macro: it is added to the slot of the flight, so a
    positive value delays the arrivals.
    The result uses the same slots as ``arrivals.presentation_curve``: the
    macro writes the value of its slot ``i`` on the row of the sheet "Paso3"
    labelled with the start time of slot ``i - 1``.
    """
    fractions = profiles[profile].to_numpy()
    pax_slots = [0] * (SLOTS_PER_DAY + 1)  # paxFranjas(0 To 288)

    for flight in flights.itertuples(index=False):
        # Integer assignment in VBA rounds to the nearest (half to even),
        # as Python's round() does
        flight_slot = round(flight.departure_minute / SLOT_MINUTES)
        later = flight_slot + oleada
        total_pax = round(flight.seats * load_factor)

        # Error: flights whose slot is 7 or lower (departure before 00:40)
        # are skipped altogether
        if later <= 7:
            continue

        # Error: the passengers are rounded interval by interval and the
        # remainder (res = totalPax - accPax) is never used
        pax_intervals = [round(total_pax * f) for f in fractions]

        # Error: the loop stops at 28, so the last interval (29) is never used;
        # arrivals that would fall before midnight are dropped; a shift that
        # moves a flight past slot 288 stops the macro (IndexError here)
        j = 0
        while j < 28 and later - j >= 1:
            pax_slots[later - j] += pax_intervals[j]
            j += 1

    return pd.Series(pax_slots[1:], index=slot_labels(), name="arrivals")


def legacy_performance(arrivals, capacity) -> pd.DataFrame:
    """Sheet "Rendimientos": queue and idle time as the workbook computes them.

    The queue is right. The idle fraction is not: the workbook computes
    ``max(0, capacity - arrivals - queue) / capacity`` with the queue at the
    end of the slot, which gives idle filters in slots that end with a queue.
    """
    rows = []
    queue = 0.0
    for a, c in zip(arrivals, capacity):
        queue = max(0.0, queue + a - c)
        idle = max(0.0, c - a - queue) / c
        rows.append((c, a, queue, idle))
    return pd.DataFrame(rows, columns=["capacity", "arrivals", "queue", "idle"],
                        index=slot_labels())
