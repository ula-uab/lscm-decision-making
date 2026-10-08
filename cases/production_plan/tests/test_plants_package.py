"""Check that the package of the notebook reproduces the numbers of
production_plan.md, and that the notebook runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import model as m  # noqa: E402
from plants.data import FORECASTS, K, REDUCED_F, REDUCED_T, T  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "production_plan.ipynb"
REDUCED_CAPACITY = {f: K[f] for f in REDUCED_F}


def test_table3_vertices_and_optimum_of_the_reduced_version():
    corners = m.vertices()
    assert corners == [(180, 200), (250, 130), (250, 200)]
    assert [m.reduced_cost_of(v) for v in corners] == [123800, 121700, 145500]
    solution = m.reduced()
    assert solution["cost"] == pytest.approx(121700)
    assert solution["plan"] == {("Plant 1", "Jan"): 250, ("Plant 2", "Jan"): 130}


def test_table4_shadow_prices_and_ranges():
    solution = m.reduced()
    assert solution["capacity price"] == {("Plant 1", "Jan"): -30, ("Plant 2", "Jan"): 0}
    assert solution["demand price"] == {"Jan": 340}
    assert solution["spare"][("Plant 2", "Jan")] == 70
    args = (REDUCED_F, REDUCED_T, {"Jan": 380}, REDUCED_CAPACITY)
    assert m.validity_range("capacity", ("Plant 1", "Jan"), *args) == (180, 380)
    assert m.validity_range("demand", "Jan", *args) == (250, 450)
    assert m.validity_range("capacity", ("Plant 2", "Jan"), *args) == (130, None)


def test_table5_plan_with_forecast_1():
    solution = m.solve(demand=FORECASTS["Forecast 1"])
    assert solution["cost"] == pytest.approx(713800)
    plan = solution["plan"]
    assert [plan["Plant 1", t] for t in T] == [250, 250, 250, 250, 250, 230]
    assert [plan["Plant 2", t] for t in T] == [130, 80, 170, 190, 180, 0]
    assert [plan["Plant 3", t] for t in T] == [0] * 6


def test_table6_shadow_prices_and_reduced_costs():
    solution = m.solve(demand=FORECASTS["Forecast 1"])
    assert [solution["demand price"][t] for t in T] == [340, 340, 340, 340, 340, 310]
    assert [solution["reduced cost"]["Plant 3", t] for t in T] == [50, 50, 50, 50, 50, 80]
    assert solution["reduced cost"]["Plant 2", "Jun"] == 30
    assert [solution["capacity price"]["Plant 1", t] for t in T] == [-30] * 5 + [0]


def test_table7_forecast_2_has_no_solution():
    demand = FORECASTS["Forecast 2"]
    assert m.solve(demand=demand) is None
    assert m.monthly_capacity() == {t: 600 for t in T}
    assert m.shortfall(demand) == {"Apr": 50, "May": 20}
    rows = m.cumulative(demand)
    assert [r["spare"] for r in rows[:3]] == [220, 270, 180]
    assert [r["cumulative demand"] for r in rows] == [380, 710, 1130, 1780, 2400, 2630]
    assert [r["cumulative capacity"] for r in rows] == [600, 1200, 1800, 2400, 3000, 3600]
    assert all(r["cumulative capacity"] >= r["cumulative demand"] for r in rows)


def test_one_source_of_data():
    # The model, the tables and the figures read the same demand and capacity
    assert m.d is FORECASTS["Forecast 1"] and m.K is K


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
