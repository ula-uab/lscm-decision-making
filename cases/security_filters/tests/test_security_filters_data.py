"""Input data: flight schedule and arrival profiles."""

import datetime as dt

import numpy as np
import pytest

from security_filters import days, flights_for_curve, flights_of_day
from security_filters.profiles import read_profiles_from_workbook

from pathlib import Path

TEMPLATE = (Path(__file__).resolve().parents[1] / "reference"
            / "ProcesaDatosVuelos-plantilla-original.xls")


def test_schedule_is_read_completely(schedule):
    assert len(schedule) == 5597
    assert schedule["seats"].between(1, 500).all()
    assert (schedule["departure_minute"] % 5 == 0).all()


def test_days_of_the_schedule(schedule):
    per_day = days(schedule)
    assert len(per_day) == 20
    assert per_day[dt.date(2008, 7, 19)] == 430
    assert per_day.index.min() == dt.date(2008, 7, 16)


def test_flights_of_day_are_sorted(schedule):
    flights = flights_of_day(schedule, "2008-07-19")
    assert len(flights) == 430
    assert flights["departure_minute"].is_monotonic_increasing


def test_flights_for_curve_add_early_flights_of_next_day(schedule):
    flights = flights_for_curve(schedule, "2008-07-19")
    next_day = flights[flights["day_offset"] == 1]
    assert (next_day["date"] == dt.date(2008, 7, 20)).all()
    assert (next_day["departure_minute"] < 29 * 5).all()
    assert len(flights) == 430 + len(next_day)


def test_profiles_csv_matches_original_workbook(profiles):
    original = read_profiles_from_workbook(TEMPLATE)
    assert list(profiles.columns) == ["gauss", "erlang", "normal2", "erlang2", "erlang3"]
    assert len(profiles) == 29
    np.testing.assert_allclose(profiles.to_numpy(), original.to_numpy(), rtol=1e-11)


def test_profiles_add_up_to_one(profiles):
    np.testing.assert_allclose(profiles.sum(), 1.0, atol=1e-6)


def test_erlang3_is_erlang2_reversed(profiles):
    """Data issue kept as it is: erlang3 is erlang2 read backwards."""
    np.testing.assert_allclose(profiles["erlang3"].to_numpy(),
                               profiles["erlang2"].to_numpy()[::-1])
