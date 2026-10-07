"""Comparison of the PPPs of several scenarios (phase 4). The expected numbers
were computed by the lecturer's design session; every value of the flights
is set here."""

import pandas as pd
import pytest

import security_filters as sf
from security_filters.comparison import summary
from security_filters.ppp import airport_ppp

DAY = "2008-07-19"
DOMESTIC = sf.PATTERNS["Domestic, mixed purpose"]


def scenario_with(schedule, load_factor, transit_share, day=DAY):
    """Every flight of the day (and early next-day flights) with the given
    L and T, the pattern Domestic, mixed purpose and no surges."""
    scenario = sf.Scenario(day, schedule=schedule)
    scenario.assign(load_factor=load_factor, transit_share=transit_share, pattern=DOMESTIC)
    return scenario


def test_numbers_of_scenarios_a_and_b(schedule):
    result = sf.compare({"A": scenario_with(schedule, 1, 0), "B": scenario_with(schedule, 0.8, 0.1)})
    assert len(result.results["A"].flights) == 430 + 12
    table = result.summary
    assert table.loc["Passengers in the day"].tolist() == [77110, 55486]
    assert table.loc["Highest value"].tolist() == [459, 334]
    assert table.loc["Slot of the highest value"].tolist() == ["08:45–08:50"] * 2
    assert [r.peak_slot for r in result.results.values()] == [105, 105]


def test_comparison_gives_the_ppp_and_summary_of_each_scenario(schedule):
    a, b = scenario_with(schedule, 1, 0), scenario_with(schedule, 0.8, 0.1)
    result = sf.compare({"A": a, "B": b})
    for name, scenario in [("A", a), ("B", b)]:
        alone = airport_ppp(scenario.flights)
        pd.testing.assert_series_equal(result.curves[name], alone.arrivals, check_names=False)
        pd.testing.assert_series_equal(result.summary[name], summary(alone), check_names=False)


def test_a_scenario_compared_with_itself(schedule):
    a = scenario_with(schedule, 0.8, 0.1)
    curves = sf.compare({"A": a, "A again": a}).curves
    assert curves["A"].equals(curves["A again"])


def test_order_of_the_scenarios_is_kept(schedule):
    result = sf.compare({"B": scenario_with(schedule, 0.8, 0.1), "A": scenario_with(schedule, 1, 0)})
    assert list(result.curves.columns) == ["B", "A"]
    assert list(result.summary.columns) == ["B", "A"]
    assert result.hourly.sum().tolist() == result.curves.sum().tolist()


def test_scenarios_of_different_days_are_rejected(schedule):
    with pytest.raises(ValueError, match="same day"):
        sf.compare({"A": scenario_with(schedule, 1, 0),
                    "C": scenario_with(schedule, 1, 0, day="2008-07-20")})


def test_comparison_panel(schedule):
    from security_filters.panel import ComparisonPanel, ScenarioPanel
    scenarios = ScenarioPanel(DAY, schedule)
    scenarios.saved["A"] = scenario_with(schedule, 1, 0).to_dict()
    scenarios.saved["B"] = scenario_with(schedule, 0.8, 0.1).to_dict()
    panel = ComparisonPanel(scenarios)
    panel.choices.value = ("A",)
    panel.compare_button.click()
    assert "at least two" in panel.message.value and panel.comparison is None
    panel.choices.value = ("A", "B")
    panel.compare_button.click()
    assert panel.comparison.summary.loc["Passengers in the day"].tolist() == [77110, 55486]
