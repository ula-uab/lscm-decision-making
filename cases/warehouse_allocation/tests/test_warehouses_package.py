"""Check that the package of the notebook reproduces the numbers of
warehouse_allocation.md, and that the notebook runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from warehouses import forecast as fc  # noqa: E402
from warehouses import model as m  # noqa: E402
from warehouses import show  # noqa: E402
from warehouses.data import K, d  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "warehouse_allocation.ipynb"

# Table 7: cost (EUR/week) and average delivery time (days) of the feasible plans
TABLE_7 = {"A": (320, 1.69), "B": (450, 1.31), "M": (465, 1.54), "D": (580, 2.38), "E": (595, 2.62)}


def test_table5_rule_of_thumb_and_model():
    assert not m.is_feasible(m.nearest_warehouse_plan())
    assert m.excess(m.nearest_warehouse_plan()) == {"W1": 25}
    assert m.diverted_by_hand_plan() == m.NAMED_PLANS["M"]
    assert m.solve() == m.NAMED_PLANS["A"]
    assert m.best_by_brute_force() == m.NAMED_PLANS["A"]
    assert m.cost(m.NAMED_PLANS["M"]) - m.cost(m.NAMED_PLANS["A"]) == 145


def test_table6_sixteen_plans_five_feasible():
    plans = m.all_plans()
    assert len(plans) == 16
    feasible = [p for p in plans if m.is_feasible(p)]
    assert sorted(m.name_of(p) for p in feasible) == sorted(TABLE_7)
    table = show.all_plans_table()
    assert list(table.index[:5]) == ["A", "B", "M", "D", "E"]
    assert list(table["Cost (€/week)"]) == [320, 450, 465, 580, 595, 290, 390, 420, 480, 495,
                                           550, 565, 625, 655, 725, 755]


def test_table7_two_objectives_and_pareto():
    feasible = [p for p in m.all_plans() if m.is_feasible(p)]
    for name, (cost, time) in TABLE_7.items():
        plan = m.NAMED_PLANS[name]
        assert m.cost(plan) == cost
        assert round(m.average_delivery_time(plan), 2) == time
    pareto = sorted(m.name_of(p) for p in feasible if m.is_pareto_optimal(p, feasible))
    assert pareto == ["A", "B"]


def test_pareto_table_says_who_beats_whom():
    table = show.pareto_table()
    assert list(table["Pareto-optimal"]) == ["yes", "yes", "no", "no", "no"]
    assert table.loc["M", "Beaten by"].startswith("B:")
    assert table.loc["D", "Beaten by"].startswith("A, B, M:")


def test_value_of_a_day_switches_from_A_to_B_at_338():
    a, b = m.NAMED_PLANS["A"], m.NAMED_PLANS["B"]
    assert m.average_delivery_time(a) - m.average_delivery_time(b) == pytest.approx(50 / 130)
    assert m.switch_value(a, b) == pytest.approx(338)
    assert round(m.total(a, 100)) == 489 and round(m.total(b, 100)) == 581
    for value in range(0, 1001, 10):
        assert m.solve_weighted(value) == m.best_weighted(value)
    assert m.best_weighted(0) == m.NAMED_PLANS["A"]
    assert m.best_weighted(337) == m.NAMED_PLANS["A"]
    assert m.best_weighted(339) == m.NAMED_PLANS["B"]
    for value in range(0, 1001, 10):
        assert m.best_weighted(value) != m.NAMED_PLANS["M"]


def test_table8_forecast_error():
    assert fc.moving_average()[4:] == [35.25, 34.75, 34.50, 35.25, 33.75, 35.00, 34.75, 34.25]
    acc = fc.accuracy()
    assert acc["MAE"] == pytest.approx(1.8125)
    assert round(acc["MAPE"], 1) == 5.4
    assert acc["bias"] == pytest.approx(-0.3125)
    assert fc.next_week() == 35


def test_large_error_and_safety_margin():
    week13 = dict(d, C3=46)
    assert m.excess(m.NAMED_PLANS["A"], K, week13) == {"W1": 6}
    assert m.solve(demand=week13) == m.NAMED_PLANS["B"]
    with_10 = m.solve(m.with_reserve(0.10))
    assert with_10 == m.NAMED_PLANS["M"]
    assert m.cost(with_10) - m.cost(m.NAMED_PLANS["A"]) == 145
    # More reserve is not always more protection: plan M does not hold the
    # order of week 13 (W2 by 1 pallet), plan B, chosen with 7 %, does
    assert m.excess(with_10, K, week13) == {"W2": 1}
    assert m.solve(m.with_reserve(0.07)) == m.NAMED_PLANS["B"]
    assert m.is_feasible(m.NAMED_PLANS["B"], K, week13)
    assert m.solve(m.with_reserve(0.15)) is None


def test_package_and_solver_scripts_agree():
    import importlib.util
    script = Path(__file__).resolve().parents[1] / "warehouse_allocation.py"
    spec = importlib.util.spec_from_file_location("warehouse_allocation_script", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.best_plan() == m.solve()
    assert module.best_plan(m.with_reserve(0.10)) == m.solve(m.with_reserve(0.10))
    assert module.diverted_by_hand_plan() == m.diverted_by_hand_plan()


def test_wrong_plan_gives_a_clear_message():
    with pytest.raises(ValueError, match="C4"):
        m.check({"C1": "W1", "C2": "W1", "C3": "W1"})
    with pytest.raises(ValueError, match="W1 or W2"):
        m.check({"C1": "W1", "C2": "W3", "C3": "W1", "C4": "W1"})


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=120, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
