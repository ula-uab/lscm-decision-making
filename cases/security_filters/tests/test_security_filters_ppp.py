"""PPP of the airport (design, §6). The expected numbers were computed by the
lecturer's design session with §6; every value of the flights is set here."""

import numpy as np
import pandas as pd
import pytest

import security_filters as sf
from security_filters.ppp import airport_ppp, flight_passengers, whole_passengers

DAY = "2008-07-19"
DOMESTIC = sf.PATTERNS["Domestic, mixed purpose"]


def all_flights(schedule, pattern=DOMESTIC):
    """Flights of 19/07/2008 (and early next-day flights) with L = 1, T = 0,
    the given pattern and no surges, set here."""
    flights = sf.Scenario(DAY, schedule=schedule).flights
    flights["load_factor"], flights["transit_share"], flights["offset"] = 1.0, 0.0, 0
    flights["pattern"] = [pattern] * len(flights)
    return flights


def surge_offsets(flights):
    """Offsets of the surge of the example of phase 2: Thomsonfly, 09:15,
    09:40, 10:40 and 10:50 (0, 5, 17 and 19 slots)."""
    offsets = pd.Series(0, index=flights.index)
    for departure, offset in [("09:15", 0), ("09:40", 5), ("10:40", 17), ("10:50", 19)]:
        offsets[(flights["airline"] == "TOM") & (flights["departure"] == departure)
                & (flights["day_offset"] == 0)] = offset
    return offsets


def test_passengers_of_a_flight():
    assert flight_passengers(122, 0.80, 0.25) == (98, 25, 73)


def test_shares_of_the_slots():
    np.testing.assert_allclose(DOMESTIC.shares(29)[:3], [0.0143, 0.0196, 0.0259], atol=5e-5)
    shuttle = sf.PATTERNS["Shuttle"].shares(29)
    np.testing.assert_allclose(shuttle[:3], [0.0379, 0.0920, 0.1255], atol=5e-5)
    for pattern in sf.PATTERNS.values():
        assert pattern.shares(29).sum() == pytest.approx(1)


def test_shares_of_a_pattern_with_no_density_in_the_slots():
    # The density is 0 in every slot: the shares would be NaN
    with pytest.raises(ValueError, match="no passenger arrives"):
        sf.normal(1000, 5.5).shares(sf.N_SLOTS)


def test_whole_passengers_of_a_flight():
    expected = [2, 3, 3, 5, 5, 7, 8, 9, 9, 10, 10, 10, 10, 8, 8, 7, 5, 5, 4, 2, 2, 2,
                0, 1, 0, 1, 0, 0, 0]
    assert whole_passengers(136, DOMESTIC.shares(29)).tolist() == expected


@pytest.mark.parametrize("name", list(sf.PATTERNS))
def test_no_negative_slot_and_sum_of_the_flight(name):
    shares = sf.PATTERNS[name].shares(29)
    for passengers in range(0, 421):
        slots = whole_passengers(passengers, shares)
        assert (slots >= 0).all() and slots.sum() == passengers


def test_ppp_of_19_july_by_default(schedule):
    result = airport_ppp(all_flights(schedule))
    assert len(result.flights) == 430 + 12
    assert result.passengers == 78543
    assert result.arrivals.sum() == 77110
    assert result.before_midnight + result.after_midnight == 1433
    assert result.arrivals.max() == 459
    assert result.peak_slot == 105 and result.arrivals.index[105] == "08:45"


def test_ppp_with_the_surge_of_the_example(schedule):
    flights = all_flights(schedule)
    flights["offset"] = surge_offsets(flights)
    result = airport_ppp(flights)
    assert result.arrivals.sum() == 77110
    assert result.arrivals.max() == 480
    assert result.arrivals.index[result.peak_slot] == "07:40"


def test_patterns_and_surges_keep_the_total_of_passengers(schedule):
    reference = airport_ppp(all_flights(schedule))
    for pattern in sf.PATTERNS.values():
        flights = all_flights(schedule, pattern)
        flights["offset"] = surge_offsets(flights)
        result = airport_ppp(flights)
        assert result.passengers == reference.passengers
        assert (result.arrivals.sum() + result.before_midnight + result.after_midnight
                == reference.passengers)


def test_slot_1_of_a_flight_ends_when_the_gate_closes(schedule):
    flights = all_flights(schedule)
    flight = flights[(flights["departure_minute"] >= 12 * 60) & (flights["day_offset"] == 0)].iloc[[0]]
    std = int(flight["departure_minute"].iloc[0]) // 5
    arrivals = airport_ppp(flight).arrivals.to_numpy()
    slots = whole_passengers(int(flight["seats"].iloc[0]), DOMESTIC.shares(29))
    assert arrivals[std - 6:std + 1].sum() == 0        # no passenger in the last 30 minutes
    assert arrivals[std - 7] == slots[0]                # slot 1 ends when the gate closes
    assert arrivals[std - 6 - 29] == slots[-1]          # slot 29


def test_ppp_of_a_scenario_uses_its_values(schedule):
    scenario = sf.Scenario(DAY, schedule=schedule)
    scenario.assign(["TOM"], load_factor=0.5, transit_share=0.2)
    result = airport_ppp(scenario.flights)
    tom = result.flights[result.flights["airline"] == "TOM"]
    expected = [flight_passengers(s, 0.5, 0.2)[2] for s in tom["seats"]]
    assert tom["passengers"].tolist() == expected


def test_ppp_panel_of_the_current_scenario_and_a_group(schedule):
    from security_filters.panel import PPPPanel, ScenarioPanel
    scenarios = ScenarioPanel(DAY, schedule)
    panel = PPPPanel(scenarios)
    panel.compute_button.click()
    assert panel.result.arrivals.sum() == airport_ppp(scenarios.scenario.flights).arrivals.sum()
    assert "Passengers in the day" in panel.summary_text.value
    scenarios.airline_box.value = ("TOM",)
    panel.show_group.value = True
    tom = scenarios.scenario.flights["airline"] == "TOM"
    assert f"{tom.sum()} flights" in panel.group_text.value
