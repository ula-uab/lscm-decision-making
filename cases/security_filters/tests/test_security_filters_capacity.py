"""Capacity plan (phase 5). The example plan of the brief, written with lanes
(lecturer, 06/10/2026: L lanes of C_L passengers per slot); every value is
set here."""

import pytest

import security_filters as sf
from security_filters.capacity import CapacityPlan

EXAMPLE = [{"start": "00:00", "lanes": 2}, {"start": "05:00", "lanes": 10},
           {"start": "12:00", "lanes": 8}, {"start": "22:00", "lanes": 2}]


def example():
    return CapacityPlan(EXAMPLE, lanes_available=10, lane_capacity=50, name="example")


def test_capacity_of_each_slot():
    capacity = example().capacity().to_numpy()
    assert len(capacity) == 288
    assert (capacity[0:60] == 100).all()
    assert (capacity[60:144] == 500).all()
    assert (capacity[144:264] == 400).all()
    assert (capacity[264:288] == 100).all()


def test_capacity_of_the_day():
    assert example().capacity().sum() == 98400


def test_maximum_capacity_is_lanes_times_lane_capacity():
    assert CapacityPlan([{"start": "00:00", "lanes": 1}], 7, 30).max_capacity == 210


def test_periods_are_kept_in_order_of_start():
    plan = CapacityPlan(list(reversed(EXAMPLE)), 10, 50)
    assert [p["start"] for p in plan.periods] == ["00:00", "05:00", "12:00", "22:00"]
    assert plan.table()["To"].tolist() == ["05:00", "12:00", "22:00", "24:00"]


@pytest.mark.parametrize("periods, message", [
    ([{"start": "01:00", "lanes": 2}], "00:00"),
    ([{"start": "00:00", "lanes": 2}, {"start": "05:00", "lanes": 3},
      {"start": "05:00", "lanes": 4}], "Two periods start at 05:00"),
    ([{"start": "00:00", "lanes": 2}, {"start": "05:02", "lanes": 3}], "on the hour"),
    ([{"start": "00:00", "lanes": 2}, {"start": "05:30", "lanes": 3}], "on the hour"),
    ([{"start": "00:00", "lanes": 0}], "from 1 to 10"),
    ([{"start": "00:00", "lanes": 11}], "from 1 to 10"),
    ([{"start": "00:00", "lanes": 2.5}], "whole number"),
])
def test_plans_that_break_the_rules_are_rejected(periods, message):
    with pytest.raises(ValueError, match=message):
        CapacityPlan(periods, lanes_available=10, lane_capacity=50)


@pytest.mark.parametrize("lanes, lane_capacity", [(0, 50), (10, 0), (10, 12.5)])
def test_parameters_must_be_whole_and_positive(lanes, lane_capacity):
    with pytest.raises(ValueError, match="whole number"):
        CapacityPlan([{"start": "00:00", "lanes": 1}], lanes, lane_capacity)


def test_saved_plan_gives_the_same_capacity(tmp_path):
    plan = example()
    loaded = CapacityPlan.load(plan.save(tmp_path / "plan.json"))
    assert loaded.name == "example"
    assert (loaded.lanes_available, loaded.lane_capacity) == (10, 50)
    assert loaded.capacity().equals(plan.capacity())


def test_plan_panel(schedule):
    from security_filters.panel import PlanPanel, ScenarioPanel
    panel = PlanPanel(ScenarioPanel("2008-07-19", schedule))
    panel.rows[0]["lanes"].value = 2
    for start, lanes in [("05:00", 10), ("12:00", 8), ("22:00", 2)]:
        panel.add_button.click()
        panel.rows[-1]["start"].value, panel.rows[-1]["lanes"].value = start, lanes
    panel.draw_button.click()
    assert "98,400" in panel.plan_message.value
    panel.add_button.click()
    panel.rows[-1]["start"].value = "05:00"
    panel.draw_button.click()
    assert "Two periods start at 05:00" in panel.plan_message.value
