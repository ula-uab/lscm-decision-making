"""Check that the package reproduces the numbers of retailers.md (M4), and that
the notebook of M4 runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import retailers as rt  # noqa: E402
from plants.data import (ARCS, ARCS_M4, BACKORDER_SHARE, F, FORECAST_5, FORECASTS, K_h_node_m4, NODES,  # noqa: E402
                         RETAILERS, SHARE_M4, T)

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "retailers.ipynb"


def months(values, key):
    return [values[key, t] for t in T]


def lost(solution):
    return {r: sum(months(solution["lost sales"], r)) for r in RETAILERS}


def test_data_of_the_retailers():
    assert ARCS_M4[:13] == ARCS and len(ARCS_M4) == 25
    assert [arc["cost"] for arc in ARCS_M4[13:]] == [0.97, 2.26, 0.92, 1.05, 1.77, 6.0, 2.24, 5.31, 1.44, 5.21,
                                                       2.54, 4.78]
    assert sum(SHARE_M4.values()) == pytest.approx(1)
    assert all(abs(o - round(o)) < 1e-9 for o in rt.orders().values())
    assert list(FORECASTS) == ["Forecast 1", "Forecast 2"]
    assert all(K_h_node_m4[r] == 0 for r in RETAILERS)


def test_m3_has_no_solution_with_forecast_5():
    assert rt.m3_has_no_solution()


def test_tables5_to_8_plan_with_forecast_5():
    solution = rt.solve()
    assert solution["cost"] == pytest.approx(1294204.84)
    assert {f: months(solution["assembly"], f) for f in F} == pytest.approx({
        "Plant 1": [250] * 6, "Plant 2": [200] * 6, "Plant 3": [0, 110, 150, 150, 150, 150]})
    assert months(solution["flow"], 21) == pytest.approx([50, 100, 90, 150, 150, 110])
    assert months(solution["flow"], 22) == pytest.approx([0, 0, 0, 30, 30, 0])
    assert months(solution["flow"], 4) == pytest.approx([100, 280, 340, 440, 480, 310])
    assert months(solution["stock"], "Central warehouse") == pytest.approx([150, 150, 150, 50, 0, 0])
    assert months(solution["deliveries"], "Retailer 3") == pytest.approx([45, 90, 81, 162, 92, 134])
    assert months(solution["deliveries"], "Retailer 6") == pytest.approx([25, 50, 45, 90, 0, 40])
    assert months(solution["backorders"], "Retailer 3") == pytest.approx([0, 0, 0, 0, 35, 0])
    assert months(solution["backorders"], "Retailer 6") == pytest.approx([0, 0, 0, 0, 36, 0])
    assert months(solution["lost sales"], "Retailer 3") == pytest.approx([0, 0, 0, 0, 35, 0])
    assert months(solution["lost sales"], "Retailer 6") == pytest.approx([0, 0, 0, 0, 54, 51])
    assert sum(solution["lost sales"].values()) == pytest.approx(140)
    for r in ["Retailer 1", "Retailer 2", "Retailer 4", "Retailer 5"]:
        assert months(solution["deliveries"], r) == pytest.approx([SHARE_M4[r] * FORECAST_5[t] for t in T])


def test_no_retailer_receives_more_than_it_ordered():
    solution = rt.solve()
    order = rt.orders()
    for r in RETAILERS:
        for k, t in enumerate(T):
            before = 0 if k == 0 else solution["backorders"][r, T[k - 1]]
            assert solution["deliveries"][r, t] <= before + order[r, t] + 1e-6


def test_the_plan_is_the_only_optimal_plan():
    assert rt.only_plan() is True


def test_table9_shadow_prices_of_the_full_capacities():
    solution = rt.solve()
    assert months(solution["arc price"], 3) == pytest.approx([0, -1.98, -1.98, -1.98, -1.98, -1.98])
    assert months(solution["arc price"], 6) == pytest.approx([0, -0.72, -0.72, -0.72, -0.72, -0.72])
    assert months(solution["arc price"], 21) == pytest.approx([0, 0, 0, -2.11, -2.11, 0])
    assert all(v == 0 for v in solution["node price"].values())
    march = {i: solution["storage price"][i, "Mar"] for i in NODES if i != "Rail terminal"}
    # In March one more bike of storage capacity at a node saves 310,17 EUR less the
    # holding cost at that node
    assert march == pytest.approx({i: -(310.17 - rt.c_h_node_m4[i]) for i in march}, abs=0.01)


def test_one_more_bike_of_storage_in_march_avoids_one_lost_sale():
    base = rt.solve()
    storage = {**K_h_node_m4, "Local warehouse 4": K_h_node_m4["Local warehouse 4"] + 1}
    solution = rt.solve(storage=storage)
    assert solution["cost"] - base["cost"] == pytest.approx(-296.17, abs=0.01)
    assert sum(solution["lost sales"].values()) == pytest.approx(139)
    assert solution["assembly"]["Plant 3", "Feb"] == pytest.approx(111)


@pytest.mark.parametrize("retailer, month, cost, total, plant_3", [
    ("Retailer 2", "Jan", 1333627.24, 140, [60, 150, 150, 150, 150, 150]),
    ("Retailer 6", "Jan", 1334132.24, 140, [60, 150, 150, 150, 150, 150]),
    ("Retailer 1", "May", 1366786.14, 240, [0, 110, 150, 150, 150, 150]),
    ("Retailer 5", "May", 1367464.14, 240, [0, 110, 150, 150, 150, 150])])
def test_promotion(retailer, month, cost, total, plant_3):
    order = rt.orders()
    order[retailer, month] += 100
    solution = rt.solve(order=order)
    assert solution["cost"] == pytest.approx(cost)
    assert sum(solution["lost sales"].values()) == pytest.approx(total)
    assert months(solution["assembly"], "Plant 3") == pytest.approx(plant_3)
    assert rt.only_plan(order=order) is True


@pytest.mark.parametrize("share, cost, alicante, cordoba, granada", [
    (0, 1291302.55, 2, 12, 126), (0.4, 1294204.84, 35, 0, 105), (0.7, 1294859.69, 80, 5, 55),
    (1, 1294859.69, 80, 5, 55)])
def test_backorder_share_of_granada(share, cost, alicante, cordoba, granada):
    solution = rt.solve(backorder_share={**BACKORDER_SHARE, "Retailer 6": share})
    assert solution["cost"] == pytest.approx(cost)
    lost_sales = lost(solution)
    assert [lost_sales["Retailer 3"], lost_sales["Retailer 5"], lost_sales["Retailer 6"]] == pytest.approx(
        [alicante, cordoba, granada])
    assert sum(lost_sales.values()) == pytest.approx(140)


@pytest.mark.parametrize("price, cost, total", [(700, 1294204.84, 140), (500, 1266204.84, 140),
                                                (400, 1251761.49, 320), (380, 1244042.86, 430),
                                                (360, 1232877.42, 682), (340, 1214696.32, 1040)])
def test_lost_sale_cost(price, cost, total):
    solution = rt.solve(lost_sale_cost={r: price for r in RETAILERS})
    assert solution["cost"] == pytest.approx(cost)
    assert sum(solution["lost sales"].values()) == pytest.approx(total)


def test_transport_cost_of_an_arc_to_a_retailer():
    arc_list = [dict(arc) for arc in ARCS_M4]
    arc_list[16]["cost"] = 0.5          # arc 17, Tarragona -> Sabadell
    solution = rt.solve(arc_list=arc_list)
    assert solution["cost"] == pytest.approx(1293858.45)
    assert months(solution["flow"], 16) == pytest.approx([55, 110, 99, 178, 174, 121])
    assert months(solution["flow"], 15) == pytest.approx([0, 0, 0, 20, 24, 0])
    # Arc 10, from regional warehouse 1 to Tarragona, is full in May
    assert months(solution["flow"], 9) == pytest.approx([90, 180, 182, 284, 300, 198])


def test_plans_without_a_constraint():
    # The sentences of §4 on what each constraint changes
    big = [dict(arc, capacity=10**5) for arc in ARCS_M4]
    assert rt.solve(arc_list=big)["cost"] == pytest.approx(1293489.64)
    assert rt.solve(node_capacity={})["cost"] == pytest.approx(1294204.84)
    room = {**K_h_node_m4, **{i: 10**5 for i in NODES if i.startswith(("Regional", "Local"))}}
    solution = rt.solve(storage=room)
    assert solution["cost"] == pytest.approx(1253280.15) and sum(solution["lost sales"].values()) == 0
    solution = rt.solve(capacity={f: {t: 10**5 for t in T} for f in F})
    assert solution["cost"] == pytest.approx(1206895.79) and sum(solution["lost sales"].values()) == 0
    solution = rt.solve(final=None)
    assert solution["cost"] == pytest.approx(1273440.04) and sum(solution["lost sales"].values()) == pytest.approx(110)


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
