"""Check that both scripts of the warehouse allocation case reproduce the
numbers of warehouse_allocation.md."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

CASE = Path(__file__).resolve().parents[1] / "cases" / "warehouse_allocation"
SCRIPTS = ["warehouse_allocation.py", "warehouse_allocation_solver.py"]


def load(script):
    spec = importlib.util.spec_from_file_location(Path(script).stem, CASE / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def optimal_plan(module, capacity=None):
    capacity = module.K if capacity is None else capacity
    if hasattr(module, "solve_model"):
        return module.solve_model(capacity)
    return module.best_plan(capacity)


PLAN_A = {"C1": "W1", "C2": "W2", "C3": "W1", "C4": "W2"}
PLAN_M = {"C1": "W1", "C2": "W1", "C3": "W2", "C4": "W2"}


@pytest.fixture(params=SCRIPTS)
def case(request):
    return load(request.param)


def test_table5_model_versus_rule_of_thumb(case):
    assert optimal_plan(case) == PLAN_A
    assert case.diverted_by_hand_plan() == PLAN_M
    assert case.cost(PLAN_A) == 320
    assert case.cost(PLAN_M) == 465
    assert not case.is_feasible(case.nearest_warehouse_plan())


def test_table6_number_of_plans(case):
    plans = case.all_plans()
    assert len(plans) == 16
    assert sum(case.is_feasible(p) for p in plans) == 5


def test_table7_pareto_optimal_plans(case):
    feasible = [p for p in case.all_plans() if case.is_feasible(p)]
    costs = sorted(case.cost(p) for p in feasible)
    assert costs == [320, 450, 465, 580, 595]
    pareto = sorted(case.cost(p) for p in feasible if case.is_pareto_optimal(p, feasible))
    assert pareto == [320, 450]
    assert round(case.average_delivery_time(PLAN_A), 2) == 1.69


def test_section6_safety_margin(case):
    reserve = {w: case.K[w] * (1 - case.reserve) for w in case.W}
    plan = optimal_plan(case, reserve)
    assert plan == PLAN_M
    assert case.cost(plan) - case.cost(PLAN_A) == 145


def test_both_scripts_print_the_same_output():
    outputs = [
        subprocess.run([sys.executable, script], cwd=CASE, capture_output=True,
                       text=True, check=True).stdout
        for script in SCRIPTS
    ]
    assert outputs[0] == outputs[1]
    assert "MAE" in outputs[0] and "1.81" in outputs[0]
