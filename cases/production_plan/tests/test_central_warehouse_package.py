"""Check that the package reproduces the numbers of central_warehouse.md (M2),
and that the notebook of M2 runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import central_warehouse as cw  # noqa: E402
from plants import plant_stock as ps  # noqa: E402
from plants.data import F, FORECAST_3, FORECASTS, T  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "central_warehouse.ipynb"


def rows(solution, key):
    return {f: [solution[key][f, t] for t in T] for f in F}


def test_m1_has_no_solution_with_forecast_3():
    assert ps.solve(demand=FORECAST_3) is None
    assert cw.m1_has_no_solution().startswith(
        "Unmet demand in Feb: from Jan to Feb the demand is 1.280 bikes, and the plants can assemble "
        "1.200 and held 30 in stock at the start, 50 bikes fewer than the demand.")


def test_forecast_3_is_not_in_the_forecasts_of_m0():
    assert list(FORECASTS) == ["Forecast 1", "Forecast 2"]


def test_table5_plan_with_forecast_3():
    solution = cw.solve()
    assert solution["cost"] == pytest.approx(928480)
    assert rows(solution, "assembly") == {"Plant 1": [250] * 6,
                                          "Plant 2": [200, 200, 200, 190, 180, 10],
                                          "Plant 3": [140, 150, 30, 0, 0, 0]}
    assert rows(solution, "shipments") == {"Plant 1": [230, 290, 250, 250, 250, 230],
                                           "Plant 2": [180, 230, 200, 190, 180, 0],
                                           "Plant 3": [120, 170, 30, 0, 0, 0]}
    assert rows(solution, "stock") == {"Plant 1": [40, 0, 0, 0, 0, 20],
                                       "Plant 2": [30, 0, 0, 0, 0, 10],
                                       "Plant 3": [20, 0, 0, 0, 0, 0]}
    assert [solution["warehouse stock"][t] for t in T] == [150, 0, 0, 0, 0, 0]
    assert [solution["served"][t] for t in T] == [380, 840, 480, 440, 430, 230]
    assert [solution["owed"][t] for t in T] == [0, 60, 0, 0, 0, 0]


def test_the_plan_is_the_only_optimal_plan():
    assert cw.only_plan() is True


def test_table6_shadow_prices_of_the_orders():
    assert [cw.solve()["orders price"][t] for t in T] == [390, 450, 390, 340, 340, 340]


def test_table7_shadow_prices_of_the_storage_capacities():
    solution = cw.solve()
    assert [solution["storage price"][f, "Jan"] for f in F] == [-55, -54, -53]
    assert solution["warehouse storage price"]["Jan"] == -52
    assert all(solution["storage price"][f, t] == 0 for f in F for t in T[1:])
    assert all(solution["warehouse storage price"][t] == 0 for t in T[1:])


def test_without_the_limit_on_the_orders_owed_at_the_end():
    solution = cw.solve(owed_end=None)
    assert solution["cost"] == pytest.approx(636660)
    assembled = {t: sum(solution["assembly"][f, t] for f in F) for t in T}
    assert assembled == {"Jan": 350, "Feb": 0, "Mar": 0, "Apr": 0, "May": 0, "Jun": 30}
    assert solution["owed"]["Jun"] == 2420


def test_cost_of_serving_late_with_forecast_2():
    on_time = cw.solve(demand=FORECASTS["Forecast 2"], late_cost=60)
    assert on_time["cost"] == pytest.approx(860260)
    assert all(on_time["owed"][t] == 0 for t in T)
    assert [on_time["assembly"]["Plant 3", t] for t in T] == [0, 0, 0, 0, 150, 0]
    late = cw.solve(demand=FORECASTS["Forecast 2"], late_cost=30)
    assert [late["owed"][t] for t in T] == [0, 0, 0, 0, 150, 0]
    assert all(late["assembly"]["Plant 3", t] == 0 for t in T)


@pytest.mark.parametrize("storage, owed_in_february, held_in_january",
                         [(50, 160, 50), (150, 60, 150), (160, 50, 160), (200, 50, 160)])
def test_storage_capacity_of_the_warehouse(storage, owed_in_february, held_in_january):
    solution = cw.solve(warehouse_storage=storage)
    assert solution["owed"]["Feb"] == owed_in_february
    assert solution["warehouse stock"]["Jan"] == held_in_january


def test_storage_capacity_of_the_plants():
    # More room at the plants: less stock at the warehouse; less room: more orders served late
    more = cw.solve(plant_storage={"Plant 1": 60, "Plant 2": 50, "Plant 3": 40})
    less = cw.solve(plant_storage={"Plant 1": 20, "Plant 2": 10, "Plant 3": 0})
    base = cw.solve()
    assert more["warehouse stock"]["Jan"] < base["warehouse stock"]["Jan"]
    assert less["owed"]["Feb"] > base["owed"]["Feb"]


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
