"""Flight data file flights.json."""

import pandas as pd
import pytest

from security_filters import airlines, airports, read_flight_data, read_schedule


@pytest.fixture(scope="module")
def data():
    return read_flight_data()


def test_every_flight_has_its_own_identifier(schedule):
    assert schedule["flight_id"].is_unique


def test_no_flight_twice_on_the_same_day(schedule):
    assert not schedule.duplicated(["date", "flight"]).any()


def test_every_destination_has_a_named_airport(schedule, data):
    table = airports(data)
    assert set(schedule["destination"]) <= set(table.index)
    named = table.loc[sorted(set(schedule["destination"]))]
    assert named[["name", "icao", "country"]].notna().all().all()


def test_every_flight_has_a_named_origin(schedule, data):
    assert schedule["origin"].notna().all()
    named = airports(data).loc[sorted(set(schedule["origin"]))]
    assert named[["name", "icao", "country"]].notna().all().all()


def test_every_airline_has_a_name(schedule, data):
    table = airlines(data)
    assert set(schedule["airline"]) <= set(table.index)
    named = table.loc[sorted(set(schedule["airline"]))]
    assert named[["name", "country"]].notna().all().all()


def test_manual_matches_cite_their_source(data):
    for table in ("airports", "airlines"):
        for code, record in data[table].items():
            if record["note"] is not None:
                assert record["source"], f"{table} {code}: note without source"


def test_schedule_can_be_read_from_the_dictionary(data, schedule):
    pd.testing.assert_frame_equal(read_schedule(data), schedule)
