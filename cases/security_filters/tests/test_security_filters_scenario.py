"""Demand scenarios: flight filters, values of groups of flights and arrival surges."""

import pandas as pd
import pytest

import security_filters as sf
from security_filters.panel import MY_NORMAL, ScenarioPanel
from security_filters.scenario import DEFAULTS

DAY = "2008-07-19"


@pytest.fixture
def scenario(schedule):
    return sf.Scenario(DAY, schedule=schedule)


def ids(scenario, airline, departures):
    flights = scenario.flights
    chosen = flights[(flights["airline"] == airline) & flights["departure"].isin(departures)]
    return list(chosen.index)


def test_day_loads_its_flights_and_early_next_day_flights(scenario, schedule):
    flights = scenario.flights
    today = flights[flights["day_offset"] == 0]
    next_day = flights[flights["day_offset"] == 1]
    assert sorted(today["flight"]) == sorted(sf.flights_of_day(schedule, DAY)["flight"])
    assert (next_day["date"].astype(str) == "2008-07-20").all()
    assert (next_day["departure_minute"] < 2 * 60 + 55).all()
    later = sf.flights_of_day(schedule, "2008-07-20")
    assert len(next_day) == (later["departure_minute"] < 2 * 60 + 55).sum()


def test_every_flight_starts_with_the_default_values(scenario):
    flights = scenario.flights
    for column, value in DEFAULTS.items():
        assert (flights[column] == value).all()
    assert (flights["offset"] == 0).all() and (flights["surge"] == "").all()


def test_filter_by_airline_and_destination(scenario):
    flights = scenario.flights
    chosen = flights[sf.scenario.select(flights, ["TOM"], ["MAN"])]
    assert len(chosen) > 0
    assert (chosen["airline"] == "TOM").all() and (chosen["destination"] == "MAN").all()
    both = (flights["airline"] == "TOM") & (flights["destination"] == "MAN")
    assert len(chosen) == both.sum()


def test_assign_changes_only_the_given_values(scenario):
    scenario.assign(["TOM"], load_factor=0.8)
    flights = scenario.flights
    tom = flights[flights["airline"] == "TOM"]
    assert (tom["load_factor"] == 0.8).all()
    assert (tom["transit_share"] == DEFAULTS["transit_share"]).all()
    assert (flights.loc[flights["airline"] != "TOM", "load_factor"] == DEFAULTS["load_factor"]).all()


def test_overlapping_assignments_last_one_wins(scenario):
    long_haul = sf.PATTERNS["Long-haul"]
    scenario.assign(["BER"], load_factor=0.8, transit_share=0.3)
    scenario.assign(["BER"], ["MAD"], load_factor=1.0, pattern=long_haul)
    flights = scenario.flights
    berlin = flights[flights["airline"] == "BER"]
    to_madrid = berlin["destination"] == "MAD"
    assert (berlin.loc[to_madrid, "load_factor"] == 1.0).all()
    assert (berlin.loc[~to_madrid, "load_factor"] == 0.8).all()
    assert (berlin["transit_share"] == 0.3).all()
    assert (berlin.loc[to_madrid, "pattern"] == long_haul).all()


def test_surge_offsets_of_the_example(scenario):
    name = scenario.surge(ids(scenario, "TOM", ["09:15", "09:40", "10:40", "10:50"]))
    surge = scenario.surges().loc[name]
    assert surge["reference"] == "TOM4814"
    assert surge["offsets"] == [0, 5, 17, 19]


def test_same_airline_two_surges_and_a_flight_in_one_surge_only(scenario):
    first = scenario.surge(ids(scenario, "TOM", ["09:15", "09:40", "10:40", "10:50"]))
    second = scenario.surge(ids(scenario, "TOM", ["09:40", "16:15"]))
    surges = scenario.surges()
    assert surges.loc[first, "flights"] == 3 and surges.loc[second, "flights"] == 2
    assert surges.loc[first, "offsets"] == [0, 17, 19]
    scenario.remove_surge(second)
    assert list(scenario.surges().index) == [first]
    assert (scenario.flights.loc[ids(scenario, "TOM", ["16:15"]), "offset"] == 0).all()


def test_surge_needs_two_flights_of_one_airline(scenario):
    with pytest.raises(ValueError, match="at least two"):
        scenario.surge(ids(scenario, "TOM", ["09:15"]))
    mixed = ids(scenario, "TOM", ["09:15"]) + ids(scenario, "EXS", ["14:30"])
    with pytest.raises(ValueError, match="one airline"):
        scenario.surge(mixed)


def test_values_out_of_range_are_rejected(scenario):
    with pytest.raises(ValueError):
        scenario.assign(load_factor=1.5)
    with pytest.raises(ValueError):
        scenario.assign()
    with pytest.raises(ValueError):
        sf.normal(10, 0)
    with pytest.raises(ValueError):
        sf.erlang(2.5, 1)
    assert scenario.steps == []


def test_saved_scenario_gives_the_same_values(scenario, schedule, tmp_path):
    scenario.assign(["TOM"], load_factor=0.95)
    scenario.assign(destinations=["MAD", "BCN"], pattern=sf.erlang(4, 0.8))
    scenario.surge(ids(scenario, "TOM", ["09:15", "09:40"]))
    scenario.name = "test"
    loaded = sf.Scenario.load(scenario.save(tmp_path / "s.json"), schedule)
    assert loaded.name == "test" and loaded.steps == scenario.steps
    pd.testing.assert_frame_equal(loaded.flights, scenario.flights)


def test_panel_lists_show_names_and_narrow_each_other(schedule):
    panel = ScenarioPanel(DAY, schedule)
    labels = dict((code, label) for label, code in panel.airline_box.options)
    assert labels["TOM"] == "Thomsonfly · TOM"
    panel.airline_box.value = ("TOM",)
    destinations = {code for _, code in panel.destination_box.options}
    flights = panel.scenario.flights
    assert destinations == set(flights.loc[flights["airline"] == "TOM", "destination"])
    assert len(panel.flight_box.options) == (flights["airline"] == "TOM").sum()


def test_a_saved_scenario_does_not_change_with_later_steps(scenario, schedule):
    scenario.assign(["TOM"], load_factor=0.95)
    saved = scenario.to_dict()
    scenario.assign(["TOM"], load_factor=0.5)
    scenario.surge(ids(scenario, "TOM", ["09:15", "09:40"]))
    assert len(saved["steps"]) == 1
    reopened = sf.Scenario.from_dict(saved, schedule)
    reopened.assign(["EZY"], load_factor=0.7)
    assert len(saved["steps"]) == 1
    tom = reopened.flights[reopened.flights["airline"] == "TOM"]
    assert (tom["load_factor"] == 0.95).all()


def test_assign_of_a_pattern_with_no_density_leaves_the_scenario_unchanged(schedule):
    panel = ScenarioPanel(DAY, schedule)
    before = panel.scenario.flights
    panel.airline_box.value = ("TOM",)
    panel.load_check.value = True
    panel.load_box.value = 0.5
    panel.pattern_check.value = True
    panel.pattern_box.value = MY_NORMAL
    panel.mu_box.value = 1000
    panel.assign_button.click()
    assert panel.scenario.steps == []
    pd.testing.assert_frame_equal(panel.scenario.flights, before)
    assert "no passenger arrives" in panel.values_text.value
    assert "#B00020" in panel.values_text.value  # shown in red
