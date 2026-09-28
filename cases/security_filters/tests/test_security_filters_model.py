"""Corrected presentation curve, queue and scenarios."""

import numpy as np
import pandas as pd
import pytest

from security_filters import (Scenario, capacity_by_hour, capacity_from_fraction,
                              capacity_from_lanes, compare, flights_for_curve,
                              flights_of_day, presentation_curve, run, simulate_queue)
from security_filters.legacy import legacy_performance


def one_flight(departure, seats=100, **extra):
    hours, minutes = departure.split(":")
    row = {"seats": seats, "departure_minute": int(hours) * 60 + int(minutes), **extra}
    return pd.DataFrame([row])


# --- Presentation curve ------------------------------------------------------

def test_flight_brings_all_its_passengers(profiles):
    curve = presentation_curve(one_flight("12:00", seats=187), profiles)
    assert curve.sum() == pytest.approx(187)


def test_first_interval_is_the_slot_just_before_departure(profiles):
    curve = presentation_curve(one_flight("12:00"), profiles, profile="gauss")
    assert curve["11:55"] == pytest.approx(100 * profiles["gauss"].loc[1])
    assert curve["12:00"] == 0
    assert curve["09:35"] == pytest.approx(100 * profiles["gauss"].loc[29])


def test_flight_just_after_midnight_counts_arrivals_after_0000(profiles):
    # Departure 00:20 = slot 4: intervals 1-4 fall in slots 3, 2, 1 and 0
    curve = presentation_curve(one_flight("00:20"), profiles, profile="gauss")
    assert curve.sum() == pytest.approx(100 * profiles["gauss"].loc[1:4].sum())
    assert curve["00:00"] == pytest.approx(100 * profiles["gauss"].loc[4])


def test_next_day_flight_arrivals_before_midnight(profiles):
    flight = one_flight("01:00", day_offset=1)
    curve = presentation_curve(flight, profiles, profile="gauss")
    # Departure at 24:00 + 60 min = slot 300; slots 287 back to 271 are today
    assert curve.sum() == pytest.approx(100 * profiles["gauss"].loc[13:29].sum())
    assert curve["23:55"] == pytest.approx(100 * profiles["gauss"].loc[13])


def test_shift_outside_the_day_does_not_fail(profiles):
    curve = presentation_curve(one_flight("23:55"), profiles, shift_slots=40)
    assert curve.sum() < 100


def test_load_factor_and_per_flight_columns(profiles):
    flights = pd.concat([one_flight("10:00", load_factor=0.5, profile="gauss"),
                         one_flight("15:00")], ignore_index=True)
    curve = presentation_curve(flights, profiles, profile="erlang", load_factor=1.0)
    assert curve.sum() == pytest.approx(150)


def test_corrected_curve_accounts_for_every_passenger(schedule, profiles):
    """Passengers in the curve of 19/07/2008 = seats of the day's flights
    - their arrivals that fall before 00:00 (they belong to 18/07)
    + arrivals before midnight of the early flights of 20/07."""
    flights = flights_for_curve(schedule, "2008-07-19")
    today = flights[flights["day_offset"] == 0]
    tomorrow = flights[flights["day_offset"] == 1]
    fractions = profiles["erlang"].to_numpy()
    intervals = np.arange(1, len(fractions) + 1)
    before_midnight = sum(f.seats * fractions[f.departure_minute // 5 - intervals < 0].sum()
                          for f in today.itertuples())
    from_tomorrow = presentation_curve(tomorrow, profiles).sum()
    curve = presentation_curve(flights, profiles)
    assert curve.sum() == pytest.approx(today["seats"].sum() - before_midnight + from_tomorrow)


# --- Queue ------------------------------------------------------------------

def test_queue_recursion_and_conservation():
    result = simulate_queue([100, 300, 50, 0], [150, 150, 150, 150])
    assert result["queue"].tolist() == [0, 150, 50, 0]
    assert result["served"].tolist() == [100, 150, 150, 50]
    assert result["served"].sum() + result["queue"].iloc[-1] == 450


def test_no_idle_time_while_there_is_a_queue(performance):
    arrivals, capacity = performance["Presentación"], performance["Capacidad Filtros"]
    result = simulate_queue(arrivals, capacity)
    workbook = legacy_performance(arrivals, capacity)
    assert (result.loc[result["queue"] > 0, "idle"] == 0).all()
    # The workbook shows idle filters in slots that end with a queue
    assert (workbook.loc[workbook["queue"] > 0, "idle"] > 0).any()
    # Elsewhere the corrected idle time is never higher than the workbook's
    assert (result["idle"].to_numpy() <= workbook["idle"].to_numpy() + 1e-12).all()


def test_queue_matches_workbook(performance):
    result = simulate_queue(performance["Presentación"], performance["Capacidad Filtros"])
    np.testing.assert_allclose(result["queue"], performance["Colas"])


# --- Scenarios ----------------------------------------------------------------

def test_capacity_helpers():
    assert capacity_from_fraction([0.1, 1.0]).tolist() == [50, 500]
    assert capacity_from_lanes([2], 180).tolist() == [30]
    hourly = capacity_by_hour({6: 300}, default=100)
    assert len(hourly) == 288 and hourly[72] == 300 and hourly[0] == 100


def test_scenarios_run_and_compare(schedule, profiles):
    flights = flights_for_curve(schedule, "2008-07-19")
    base = Scenario("base", capacity=500)
    tight = Scenario("tight", capacity=300)
    result = run(base, flights, profiles)
    assert len(result) == 288
    table = compare([base, tight], flights, profiles)
    assert table.loc["max_queue", "tight"] >= table.loc["max_queue", "base"]
    assert table.loc["passengers", "base"] == pytest.approx(table.loc["passengers", "tight"])
