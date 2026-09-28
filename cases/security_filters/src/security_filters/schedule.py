"""Read the flight schedule and select the flights of one day.

The schedule is the Excel file of the original case (``mostradores.xls``,
copied as ``data/flight_schedule.xls``). Each row is a departing flight:
date, flight number, departure time, destination airport and number of seats.
"""

from __future__ import annotations

import datetime as dt
from importlib import resources
from pathlib import Path

import pandas as pd

SLOT_MINUTES = 5
SLOTS_PER_DAY = 24 * 60 // SLOT_MINUTES  # 288

# Column names of the original workbook and the names used in this package
SOURCE_COLUMNS = {
    "F. Vuelo": "date",
    "Linea": "flight",
    "Hora": "departure",
    "Des": "destination",
    "Numero asientos aeronave": "seats",
}


def default_schedule_path() -> Path:
    """Path of the flight schedule shipped with the package."""
    return Path(str(resources.files("security_filters") / "data" / "flight_schedule.xls"))


def read_schedule(path: str | Path | None = None, header_row: int = 2) -> pd.DataFrame:
    """Read the whole flight schedule.

    Returns one row per flight with the columns ``date`` (datetime.date),
    ``flight``, ``departure`` (text "HH:MM"), ``destination``, ``seats`` (int)
    and ``departure_minute`` (minutes after midnight).
    """
    path = default_schedule_path() if path is None else Path(path)
    raw = pd.read_excel(path, header=header_row, engine="xlrd")
    missing = set(SOURCE_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Columns not found in {path.name}: {sorted(missing)}")

    df = raw[list(SOURCE_COLUMNS)].rename(columns=SOURCE_COLUMNS).dropna(how="all")
    if pd.api.types.is_numeric_dtype(df["date"]):
        # Dates stored as numbers: days since 30/12/1899, as Excel counts them
        df["date"] = pd.to_datetime(df["date"], unit="D", origin="1899-12-30")
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["departure"] = df["departure"].astype(str).str.strip()
    df["flight"] = df["flight"].astype(str).str.strip()
    df["destination"] = df["destination"].astype(str).str.strip()
    df["seats"] = df["seats"].astype(int)
    df["departure_minute"] = df["departure"].map(_minutes_after_midnight)
    return df.reset_index(drop=True)


def days(schedule: pd.DataFrame) -> pd.Series:
    """Number of flights of each day in the schedule."""
    return schedule.groupby("date").size().rename("flights")


def flights_of_day(schedule: pd.DataFrame, day: dt.date | str) -> pd.DataFrame:
    """Flights that depart on ``day``, ordered by departure time."""
    day = _as_date(day)
    selected = schedule[schedule["date"] == day]
    return selected.sort_values("departure_minute", kind="stable").reset_index(drop=True)


def flights_for_curve(schedule: pd.DataFrame, day: dt.date | str,
                      max_slots_before: int = 29) -> pd.DataFrame:
    """Flights whose passengers can arrive at the filters on ``day``.

    These are the flights of ``day`` and the flights of the next day that
    depart early enough for some of their passengers to arrive before
    midnight. The column ``day_offset`` is 0 for the flights of ``day`` and 1
    for those of the next day.
    """
    day = _as_date(day)
    today = flights_of_day(schedule, day).assign(day_offset=0)
    tomorrow = flights_of_day(schedule, day + dt.timedelta(days=1))
    early = tomorrow[tomorrow["departure_minute"] < max_slots_before * SLOT_MINUTES]
    return pd.concat([today, early.assign(day_offset=1)], ignore_index=True)


def _minutes_after_midnight(text: str) -> int:
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


def _as_date(day: dt.date | str) -> dt.date:
    if isinstance(day, dt.datetime):
        return day.date()
    if isinstance(day, dt.date):
        return day
    return dt.date.fromisoformat(day)
