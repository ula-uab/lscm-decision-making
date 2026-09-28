"""Distributions, rules, demand scenarios, lane policies and observed curve."""

import numpy as np
import pandas as pd
import pytest

import security_filters as sf


@pytest.fixture(scope="module")
def library():
    return sf.profile_library()


@pytest.fixture(scope="module")
def flights(schedule):
    return sf.flights_for_curve(schedule, "2008-07-19")


# --- Distributions -------------------------------------------------------------

def test_gamma_profile_has_the_requested_mean_and_sd():
    profile = pd.DataFrame({"p": sf.gamma_profile(100, 30)},
                           index=pd.RangeIndex(1, 49, name="interval_before_departure"))
    stats = sf.describe(profile).loc["p"]
    assert profile["p"].sum() == pytest.approx(1)
    assert stats["mean_min"] == pytest.approx(100, abs=1)
    assert stats["sd_min"] == pytest.approx(30, abs=1)


def test_library_keeps_original_profiles(library, profiles):
    assert len(library) == 48
    np.testing.assert_allclose(library.loc[1:29, "erlang"], profiles["erlang"])
    assert (library.loc[30:, "erlang"] == 0).all()
    np.testing.assert_allclose(library.sum(), 1.0, atol=1e-6)


def test_legacy_curve_unchanged_with_longer_profiles(schedule, library, hypotheses):
    from security_filters.legacy import legacy_presentation_curve
    curve = legacy_presentation_curve(sf.flights_of_day(schedule, "2008-07-19"), library)
    np.testing.assert_array_equal(curve.to_numpy(), hypotheses["Pax-sc1"].to_numpy())


# --- Rules ------------------------------------------------------------------------

def test_rules_later_rule_wins_and_passengers(flights):
    table = sf.apply_rules(flights, [
        {"load_factor": 0.8, "profile": "leisure"},
        {"airline": "AEA", "load_factor": 0.5, "transfer_share": 0.2},
        {"flight": flights.loc[flights["airline"] == "AEA", "flight"].iloc[0], "advance_min": 30},
    ])
    aea = table[table["airline"] == "AEA"]
    other = table[table["airline"] != "AEA"]
    assert (other["load_factor"] == 0.8).all() and (other["transfer_share"] == 0).all()
    assert (aea["load_factor"] == 0.5).all()
    np.testing.assert_allclose(aea["passengers"], aea["seats"] * 0.5 * 0.8)
    assert (table["advance_min"] == 30).sum() == 1
    assert aea["rules"].iloc[0] == "1 2 3"


def test_rules_time_window_and_lists(flights):
    table = sf.apply_rules(flights, [{"destination": ["LGW", "MAN"], "departure_from": "16:00",
                                      "departure_to": "18:00", "profile": "wave"}])
    chosen = table[table["profile"] == "wave"]
    assert chosen["destination"].isin(["LGW", "MAN"]).all()
    assert chosen["departure_minute"].between(16 * 60, 18 * 60 - 1).all()
    assert len(chosen) > 0


def test_rules_reject_unknown_keys_and_bad_values(flights):
    with pytest.raises(ValueError, match="unknown keys"):
        sf.apply_rules(flights, [{"airlines": "TOM"}])
    with pytest.raises(ValueError, match="between 0 and 1"):
        sf.apply_rules(flights, [{"load_factor": 1.2}])


def test_rules_from_csv(tmp_path, flights):
    path = tmp_path / "rules.csv"
    path.write_text("airline,destination,load_factor,advance_min,profile\n"
                    ",,0.9,,leisure\n"
                    "TOM,,,40,wave\n"
                    ",\"MAD, BCN\",,,business\n")
    rules = sf.read_rules(path)
    assert rules == [{"load_factor": 0.9, "profile": "leisure"},
                     {"airline": "TOM", "advance_min": 40, "profile": "wave"},
                     {"destination": ["MAD", "BCN"], "profile": "business"}]
    table = sf.apply_rules(flights, rules)
    assert (table.loc[table["airline"] == "TOM", "profile"] == "wave").all()


# --- Demand scenarios ---------------------------------------------------------------

def test_scenario_curve_holds_the_passengers(flights, library):
    scenario = sf.DemandScenario("mid-day", [{"load_factor": 0.9, "profile": "leisure",
                                              "departure_from": "10:00", "departure_to": "20:00"},
                                             {"departure_to": "10:00", "load_factor": 0},
                                             {"departure_from": "20:00", "load_factor": 0}])
    table = scenario.assumptions(flights)
    curve = scenario.curve(flights, library)
    assert curve.sum() == pytest.approx(table["passengers"].sum())


def test_demand_curves_one_column_per_scenario(flights, library):
    curves = sf.demand_curves([sf.DemandScenario("a", [{"profile": "leisure"}]),
                               sf.DemandScenario("b", [{"profile": "business"}])], flights, library)
    assert list(curves.columns) == ["a", "b"] and len(curves) == 288


def test_repeated_names_are_rejected(flights, library):
    with pytest.raises(ValueError, match="repeated"):
        sf.demand_curves([sf.DemandScenario("a"), sf.DemandScenario("a")], flights, library)
    curves = pd.DataFrame({"x": np.zeros(288)}, index=sf.slot_labels())
    with pytest.raises(ValueError, match="repeated"):
        sf.decision_table([sf.LanePlan("p", {}), sf.LanePlan("p", {})], curves)


# --- Lane policies ------------------------------------------------------------------

def test_lane_plan_capacity_and_cost():
    plan = sf.LanePlan("p", {"06:00-12:00": 10, "12:00-24:00": 4}, pax_per_lane_hour=180, default_lanes=2)
    lanes = plan.lanes()
    assert lanes[0] == 2 and lanes[72] == 10 and lanes[143] == 10 and lanes[144] == 4
    assert plan.capacity()[72] == 150
    assert plan.lane_hours() == 6 * 2 + 6 * 10 + 12 * 4


def test_lane_plan_rejects_bad_periods():
    with pytest.raises(ValueError):
        sf.LanePlan("p", {"12:00-06:00": 3}).lanes()
    with pytest.raises(ValueError):
        sf.LanePlan("p", {"noon": 3}).lanes()


def test_decision_table_regret_and_worst_case():
    curves = pd.DataFrame({"low": np.full(288, 100.0), "high": np.full(288, 200.0)},
                          index=sf.slot_labels())
    small = sf.LanePlan("small", {"00:00-24:00": 8}, pax_per_lane_hour=180)   # 120 per slot
    large = sf.LanePlan("large", {"00:00-24:00": 16}, pax_per_lane_hour=180)  # 240 per slot
    table = sf.decision_table([small, large], curves, "max_queue")
    assert table.loc["small", "low"] == 0 and table.loc["small", "high"] == 80 * 288
    assert table.loc["large", "high"] == 0
    assert table.loc["large", "lane_hours"] == 16 * 24
    assert sf.worst_case(table)["large"] == 0
    assert sf.regret(table).loc["small", "max_regret"] == 80 * 288


def test_lanes_to_cover():
    curve = pd.Series(np.r_[np.full(144, 30.0), np.full(144, 60.0)], index=sf.slot_labels())
    guess = sf.lanes_to_cover(curve, ["00:00-12:00", "12:00-24:00"], pax_per_lane_hour=180)
    assert guess == {"00:00-12:00": 2, "12:00-24:00": 4}


def test_capacity_helpers():
    assert sf.capacity_from_fraction([0.1, 1.0]).tolist() == [50, 500]
    assert sf.capacity_from_lanes([2], 180).tolist() == [30]
    hourly = sf.capacity_by_hour({6: 300}, default=100)
    assert len(hourly) == 288 and hourly[72] == 300 and hourly[0] == 100


# --- Observed curve ---------------------------------------------------------------------

def test_observed_curve():
    observed = sf.read_observed()
    assert len(observed) == 288 and observed.sum() == 66619
    assert (observed >= 0).all()


def test_forecast_errors():
    observed = pd.Series(np.full(288, 10.0), index=sf.slot_labels())
    forecast = pd.Series(np.full(288, 8.0), index=sf.slot_labels())
    errors = sf.forecast_errors(forecast, observed)
    assert errors["MAE"] == pytest.approx(24) and errors["bias"] == pytest.approx(24)
    assert errors["MAPE"] == pytest.approx(0.2)
    assert sf.forecast_errors(forecast, observed, by="slot")["MAE"] == pytest.approx(2)
