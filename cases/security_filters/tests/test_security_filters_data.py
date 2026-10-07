"""Input data: flight schedule."""

import datetime as dt

from security_filters import days, flights_for_curve, flights_of_day


def test_schedule_is_read_completely(schedule):
    # The 16 days with the complete schedule, without OBE7113 and 8 repeated
    # flights (lecturer, 05/10/2026 and 07/10/2026)
    assert len(schedule) == 5561
    assert schedule["seats"].between(30, 500).all()
    assert (schedule["departure_minute"] % 5 == 0).all()


def test_days_of_the_schedule(schedule):
    per_day = days(schedule)
    assert len(per_day) == 16
    assert per_day[dt.date(2008, 7, 19)] == 430
    assert per_day.index.min() == dt.date(2008, 7, 16)
    assert per_day.index.max() == dt.date(2008, 7, 31)


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
