"""Queue at security screening (phase 6). The expected numbers were computed by the
lecturer's design session with the queue model of the brief; the data are
set here. Tests 2 and 3 use the real PPPs: if the generator changes, their
numbers are computed again, the code is not adjusted."""

import pytest

import security_filters as sf
from security_filters.capacity import CapacityPlan
from security_filters.queues import apply_plan

EXAMPLE_PLAN = CapacityPlan([{"start": "00:00", "lanes": 2}, {"start": "05:00", "lanes": 10},
                             {"start": "12:00", "lanes": 8}, {"start": "22:00", "lanes": 2}],
                            lanes_available=10, lane_capacity=50)


def test_small_example():
    result = apply_plan([150, 120, 30, 0] + [0] * 284, [100] * 288)
    day = result.day
    assert day["queue"].iloc[:4].tolist() == [50, 70, 0, 0]
    assert day["served"].iloc[:4].tolist() == [100, 100, 100, 0]
    assert day["unused"].iloc[:4].tolist() == [0, 0, 0, 100]
    assert day["queue"].sum() == 120
    assert result.mean_wait_min == pytest.approx(2.00)
    assert result.longest_wait_min == 5


@pytest.mark.parametrize("day, passengers, highest, sum_queues, mean, longest, unused", [
    ("2008-07-26", 64256, 3509, 90592, 7.05, 65, 34144),
    ("2008-07-19", 63230, 4077, 125889, 9.95, 75, 35170),
])
def test_real_ppp_with_the_example_plan(day, passengers, highest, sum_queues, mean, longest, unused):
    result = apply_plan(sf.real_ppp(day), EXAMPLE_PLAN.capacity())
    assert result.passengers == passengers
    assert result.queue_at_midnight == 0
    assert result.highest_queue == highest
    assert result.day.index[result.highest_queue_slot] == "04:55"
    assert result.slots["queue"].sum() == sum_queues
    assert round(result.mean_wait_min, 2) == mean
    assert result.longest_wait_min == longest
    assert result.unused_capacity == unused == 98400 - passengers


@pytest.mark.parametrize("day", ["2008-07-16", "2008-07-22", "2008-07-31"])
def test_conservation(day):
    plan = CapacityPlan([{"start": "00:00", "lanes": 3}, {"start": "07:00", "lanes": 6}],
                        lanes_available=10, lane_capacity=50)
    result = apply_plan(sf.real_ppp(day), plan.capacity())
    day_slots = result.day
    assert day_slots["served"].sum() + result.queue_at_midnight == result.passengers
    assert day_slots["unused"].sum() + day_slots["served"].sum() == plan.capacity().sum()


def test_queue_left_at_midnight_goes_through_after_it():
    # 300 passengers arrive in the last slot; the capacity is 100 per slot
    result = apply_plan([0] * 287 + [300], [100] * 288)
    assert result.queue_at_midnight == 200
    assert result.slots["served"].iloc[288:].tolist() == [100, 100]
    assert result.cleared_after_midnight_min == 10
    assert result.longest_wait_min == 10            # the last 100 go through two slots later
    assert result.mean_wait_min == pytest.approx(5 * (200 + 100) / 300)


def test_hourly_table_adds_up():
    result = apply_plan(sf.real_ppp("2008-07-26"), EXAMPLE_PLAN.capacity())
    hourly = result.hourly()
    assert len(hourly) == 24
    assert hourly["arrivals"].sum() == result.passengers
    assert hourly["queue"].iloc[4] == result.day["queue"].iloc[59]


def test_queue_panel_and_real_ppp_in_the_comparison(schedule):
    from security_filters.panel import ComparisonPanel, PlanPanel, QueuePanel, ScenarioPanel
    scenarios = ScenarioPanel("2008-07-26", schedule)
    plans = PlanPanel(scenarios)
    plans.saved["example"] = EXAMPLE_PLAN.to_dict() | {"name": "example"}
    panel = QueuePanel(scenarios, plans)
    panel._update_plans()
    panel.plan_choice.value = "example"
    panel.day_choice.value = "2008-07-26"
    panel.apply_button.click()
    assert "7.05 minutes" in panel.summary_text.value and "3,509" in panel.summary_text.value

    comparison = ComparisonPanel(scenarios)
    scenarios.saved["A"] = scenarios.scenario.to_dict()
    scenarios.saved["B"] = scenarios.scenario.to_dict()
    comparison._update_choices()
    comparison.choices.value = ("A", "B")
    comparison.real_box.value = True
    comparison.compare_button.click()
    assert list(comparison.summary_shown.columns) == ["A", "B", "Real PPP"]
