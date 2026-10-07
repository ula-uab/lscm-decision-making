"""Passengers who miss the closing of their gate (phase 8). The expected
numbers of tests 1 and 2 were set in the brief; test 3 uses the real PPPs:
if the generator changes, its number is computed again, the code is not
adjusted."""

import numpy as np
import pandas as pd

import security_filters as sf
from security_filters.capacity import CapacityPlan
from security_filters.missed import (HORIZON, MORE, missed_with_real, missed_with_scenario,
                                     read_real_gate)
from security_filters.queues import apply_plan

STD = 600                    # 10:00: the gate closes at 09:30, at the end of slot 113
LAST_SLOT = STD // 5 - sf.GATE_SLOTS - 1


def one_flight(passengers: int) -> pd.DataFrame:
    """A flight whose passengers all arrive in the slot that ends when its
    gate closes."""
    return pd.DataFrame({
        "flight": ["XX0001"], "airline": ["XXX"], "destination": ["AAA"],
        "seats": [passengers], "load_factor": [1.0], "transit_share": [0.0],
        "pattern": [sf.normal(1, 0.01)], "offset": [0], "departure_minute": [STD],
        "day_offset": [0]}, index=pd.Index(["F1"], name="flight_id"))


def queue_of(flights: pd.DataFrame, capacity: int):
    arrivals = sf.airport_ppp(flights).arrivals
    assert arrivals.iloc[LAST_SLOT] == arrivals.sum() == flights["seats"].iloc[0]
    return apply_plan(arrivals, [capacity] * 288)


def test_one_flight_with_a_queue():
    flights = one_flight(150)
    result = missed_with_scenario(flights, queue_of(flights, 100), walk_min=0)
    assert (result.by_queue, result.anyway, result.complete) == (50, 0, True)
    assert result.flights["Miss the closing"].tolist() == [50]


def test_walk_with_no_queue():
    flights = one_flight(150)
    result = missed_with_scenario(flights, queue_of(flights, 500), walk_min=5)
    assert (result.by_queue, result.anyway) == (0, 150)
    assert result.flights.empty


SOLUTION_PLAN = CapacityPlan(
    [{"start": f"{h:02d}:00", "lanes": n} for h, n in
     [(0, 1), (2, 2), (3, 5), (4, 6), (5, 7), (6, 9), (9, 6), (11, 5), (13, 4), (14, 5),
      (15, 6), (17, 5), (18, 4), (19, 3), (20, 2), (21, 1)]],
    lanes_available=10, lane_capacity=50)


def test_real_ppp_of_22_07_with_the_plan_of_the_solution():
    queue = apply_plan(sf.real_ppp("2008-07-22"), SOLUTION_PLAN.capacity())
    assert queue.longest_wait_min == 55
    result = missed_with_real("2008-07-22", queue, walk_min=0)
    assert (result.by_queue, result.anyway, result.complete) == (716, 0, True)
    assert result.flights is None and result.by_hour.sum() == 716


def test_closing_of_the_gates_adds_up_to_the_real_ppp():
    for day in sf.read_real_ppps().columns:
        table = read_real_gate(day)
        assert list(table.columns) == [str(k) for k in range(1, HORIZON + 1)] + [MORE]
        assert np.array_equal(table.sum(axis=1).to_numpy(), sf.real_ppp(day).to_numpy())


def test_a_long_wait_makes_the_count_a_lower_bound():
    queue = apply_plan(sf.real_ppp("2008-07-22"), [50] * 288)
    assert not missed_with_real("2008-07-22", queue).complete


def test_queue_panel_with_a_scenario_as_demand():
    from security_filters.panel import PlanPanel, QueuePanel, ScenarioPanel
    scenarios = ScenarioPanel("2008-07-22")
    scenarios.saved["default"] = scenarios.scenario.to_dict() | {"name": "default"}
    plans = PlanPanel(scenarios)
    plans.saved["solution"] = SOLUTION_PLAN.to_dict() | {"name": "solution"}
    panel = QueuePanel(scenarios, plans)
    panel._update_plans()
    panel.plan_choice.value = "solution"
    panel.demand_choice.value = "default"
    assert panel.day_choice.disabled and panel.day_choice.value == "2008-07-22"
    panel.apply_button.click()
    assert "scenario 'default'" in panel.message.value
    assert "after their gate closes" in panel.summary_text.value or "No passenger" in panel.summary_text.value
