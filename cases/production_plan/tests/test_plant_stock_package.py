"""Check that the package reproduces the numbers of plant_stock.md (M1), and that
the notebook of M1 runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import plant_stock as ps  # noqa: E402
from plants.data import F, FORECASTS, T, h_0, h_end  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "plant_stock.ipynb"


def rows(solution, key, months=T):
    return {f: [solution[key][f, t] for t in months] for f in F}


def test_table4_plan_with_the_final_stock_target():
    solution = ps.solve()
    assert solution["cost"] == pytest.approx(858460)
    assert rows(solution, "assembly") == {"Plant 1": [250] * 6,
                                          "Plant 2": [200, 200, 200, 200, 200, 10],
                                          "Plant 3": [0, 0, 0, 0, 120, 0]}
    assert rows(solution, "shipments") == {"Plant 1": [170, 130, 220, 450, 300, 230],
                                           "Plant 2": [210, 200, 200, 200, 200, 0],
                                           "Plant 3": [0, 0, 0, 0, 120, 0]}
    assert rows(solution, "stock") == {"Plant 1": [100, 220, 250, 50, 0, 20],
                                       "Plant 2": [0, 0, 0, 0, 0, 10],
                                       "Plant 3": [0] * 6}


def test_table5_shadow_prices_of_the_demand():
    assert [ps.solve()["demand price"][t] for t in T] == [370, 375, 380, 385, 390, 340]
    assert [ps.solve(final=None)["demand price"][t] for t in T] == [370, 375, 380, 385, 390, 310]


def test_table6_plan_without_the_final_stock_target():
    target, free = ps.solve(), ps.solve(final=None)
    assert free["cost"] == pytest.approx(848700)
    for key in ("assembly", "shipments", "stock"):
        for f in F:
            for t in T[:-1]:
                assert free[key][f, t] == target[key][f, t]
    assert [free["assembly"][f, "Jun"] for f in F] == [230, 0, 0]
    assert [free["stock"][f, "Jun"] for f in F] == [0, 0, 0]


def test_table7_horizon_from_january_to_march_then_april_to_june():
    first = ps.solve(months=T[:3])
    assert first["cost"] == pytest.approx(361860)
    assert rows(first, "assembly", T[:3]) == {"Plant 1": [250, 250, 250], "Plant 2": [100, 80, 200],
                                              "Plant 3": [0, 0, 0]}
    left = {f: first["stock"][f, "Mar"] for f in F}
    assert left == h_end
    assert ps.solve(months=T[3:], initial=left) is None
    assert ps.why_no_plan(months=T[3:], initial=left).startswith(
        "Capacity falls short in Apr: in Apr the demand is 650 bikes, the plants can assemble 600 "
        "and they held 30 in stock at the start: 20 bikes short.")


@pytest.mark.parametrize("months, final", [(T, h_end), (T, None), (T[:3], h_end)])
def test_each_plan_is_the_only_optimal_plan(months, final):
    assert ps.only_plan(months=months, final=final) is True


def test_holding_cost_of_25_gives_several_optimal_plans():
    # The notebook warns when the plan it shows is one of several with the same cost
    assert ps.only_plan(holding={"Plant 1": 25, "Plant 2": 26, "Plant 3": 27}) is False
    assert ps.only_plan(holding={"Plant 1": 5, "Plant 2": 6, "Plant 3": 7}) is True


def test_shortage_of_plants_1_and_2_with_forecast_2():
    demand = FORECASTS["Forecast 2"]
    assert {t: demand[t] - 450 for t in T if demand[t] > 450} == {"Apr": 200, "May": 170}


def test_holding_a_bike_to_the_end_costs_less_than_assembling_it():
    # Shipping more bikes than the demand would only lower the cost otherwise
    assert 6 * max(ps.c_h.values()) < min(ps.c.values())


def test_initial_and_final_stock():
    assert h_0 == {"Plant 1": 20, "Plant 2": 10, "Plant 3": 0} and h_end == h_0


def test_no_solution_when_the_demand_is_above_capacity_and_stock():
    demand = dict(FORECASTS["Forecast 2"], Jun=1500)
    assert ps.solve(demand=demand) is None
    assert ps.why_no_plan(demand=demand).startswith("Capacity falls short in Jun")


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
