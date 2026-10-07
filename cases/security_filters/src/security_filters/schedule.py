"""Read the flight schedule and select the flights of one day.

The flights are read from ``data/flights.json``. Each record is a departing
flight: date, flight number, origin and destination airports, departure time
and number of seats. The JSON also has the names of the airlines and of the
airports.
"""

from __future__ import annotations

import datetime as dt
import json
import urllib.request
from importlib import resources
from pathlib import Path

import pandas as pd

SLOT_MINUTES = 5
SLOTS_PER_DAY = 24 * 60 // SLOT_MINUTES  # 288

# Field names of flights.json and the column names used in this package
JSON_FIELDS = {
    "id": "flight_id",
    "flight_number": "flight",
    "std": "departure",
}


def default_flight_data_path() -> Path:
    """Path of the flight data shipped with the package."""
    return Path(str(resources.files("security_filters") / "data" / "flights.json"))


def read_flight_data(source: str | Path | None = None) -> dict:
    """Read ``flights.json`` as it is: a dictionary with the flights, the
    airlines, the airports and the sources of the data.

    ``source`` can be a path or a URL (for example, the raw file on GitHub).
    By default, the file shipped with the package is read.
    """
    if source is None:
        source = default_flight_data_path()
    if str(source).startswith(("http://", "https://")):
        with urllib.request.urlopen(str(source)) as response:
            return json.loads(response.read().decode("utf-8"))
    return json.loads(Path(source).read_text(encoding="utf-8"))


def read_schedule(source: str | Path | dict | None = None) -> pd.DataFrame:
    """Read all the flights.

    ``source`` is a path or URL of ``flights.json``, or the dictionary returned
    by ``read_flight_data``. Returns one row per flight with the columns
    ``flight_id``, ``date`` (datetime.date), ``flight``, ``airline`` (ICAO
    code), ``origin`` and ``destination`` (IATA codes), ``departure`` (text
    "HH:MM", local time at the origin), ``seats`` (int), any other attribute
    of the flights in the file, and
    ``departure_minute`` (minutes after midnight).
    """
    data = source if isinstance(source, dict) else read_flight_data(source)
    df = pd.DataFrame(data["flights"]).rename(columns=JSON_FIELDS)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["seats"] = df["seats"].astype(int)
    df["departure_minute"] = df["departure"].map(_minutes_after_midnight)
    return df


def airlines(source: str | Path | dict | None = None) -> pd.DataFrame:
    """Airlines of the flights, indexed by ICAO code, with their IATA code,
    name and country."""
    data = source if isinstance(source, dict) else read_flight_data(source)
    return pd.DataFrame.from_dict(data["airlines"], orient="index").rename_axis("airline")


def airports(source: str | Path | dict | None = None) -> pd.DataFrame:
    """Airports of the flights (origin and destinations), indexed by the IATA
    code used in the flights, with their ICAO code, name, city and country."""
    data = source if isinstance(source, dict) else read_flight_data(source)
    return pd.DataFrame.from_dict(data["airports"], orient="index").rename_axis("airport")


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
    """Flights whose passengers can arrive at the security checkpoint on ``day``.

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
