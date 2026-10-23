"""Check that the package reproduces the numbers of distribution_network.md (M3),
and that the notebook of M3 runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import distribution_network as dn  # noqa: E402
from plants.data import ARCS, F, FORECAST_4, FORECASTS, K_h_node, LOCAL, NODES, SHARE, T, arcs  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "distribution_network.ipynb"


def months(values, key):
    return [values[key, t] for t in T]


def test_table2_list_of_arcs():
    assert len(ARCS) == 13
    assert [arc["cost"] for arc in ARCS] == [2.62, 1.82, 3.23, 4.27, 3.11, 2.02, 0.28, 3.3, 1.02, 0.97, 3.51, 3.6, 5.26]
    assert [arc["capacity"] for arc in ARCS] == [300, 300, 300, 60, 600, 400, 200, 150, 300, 300, 300, 300, 300]
    assert ARCS[dn.RAIL_ARC]["km"] == 336.0


def test_table4_orders_of_the_local_warehouses():
    assert sum(SHARE.values()) == pytest.approx(1)
    assert [SHARE["Local warehouse 4"] * FORECAST_4[t] for t in T] == pytest.approx([84, 154, 140, 280, 294, 175])
    assert list(FORECASTS) == ["Forecast 1", "Forecast 2"]


def test_m2_has_no_solution_with_forecast_4():
    assert dn.m2_has_no_solution()
    # 340 bikes assembled before April and the 30 of the required ending stock of the
    # plants: M2 has a solution only if the plants and the central warehouse hold 370
    from plants import central_warehouse as cw
    assert cw.solve(demand=FORECAST_4, warehouse_storage=370 - 90 - 1) is None
    assert cw.solve(demand=FORECAST_4, warehouse_storage=370 - 90) is not None


def test_tables6_to_8_plan_with_forecast_4():
    solution = dn.solve()
    assert solution["cost"] == pytest.approx(1112018.47)
    assert {f: months(solution["assembly"], f) for f in F} == {
        "Plant 1": [250] * 6, "Plant 2": [200] * 6, "Plant 3": [0, 0, 140, 150, 150, 80]}
    assert [months(solution["flow"], a) for a in range(13)] == [
        [230, 250, 250, 250, 290, 230], [180, 200, 200, 200, 230, 190], [0, 0, 60, 90, 110, 20],
        [0, 0, 60, 60, 60, 60], [104, 250, 310, 354, 546, 240], [156, 200, 200, 200, 200, 200],
        [156, 200, 200, 200, 200, 200], [0, 0, 0, 0, 20, 0], [36, 66, 80, 100, 126, 75],
        [48, 88, 100, 140, 168, 100], [0, 86, 100, 174, 252, 65], [72, 46, 40, 46, 0, 85],
        [84, 154, 160, 260, 294, 175]]
    stock = {i: months(solution["stock"], i) for i in NODES}
    assert stock["Plant 1"] == [40, 40, 40, 40, 0, 20] and stock["Plant 2"] == [30, 30, 30, 30, 0, 10]
    assert stock["Plant 3"] == [0, 0, 20, 20, 0, 0] and stock["Central warehouse"] == [150, 150, 150, 136, 0, 0]
    assert stock["Rail terminal"] == [0] * 6
    assert stock["Regional warehouse 1"] == [20, 30, 60, 0, 0, 0]
    assert stock["Regional warehouse 2"] == [0, 0, 60, 14, 0, 0]
    assert all(stock[i] == [0, 0, 20, 0, 0, 0] for i in LOCAL)
    assert all(solution["deliveries"][i, t] == pytest.approx(SHARE[i] * FORECAST_4[t]) for i in LOCAL for t in T)
    assert all(v == 0 for v in solution["backorders"].values())


def test_the_plan_is_the_only_optimal_plan():
    assert dn.only_plan() is True


def test_table9_shadow_prices_of_the_full_capacities():
    solution = dn.solve()
    assert months(solution["arc price"], 3) == pytest.approx([0, 0, -1.98, -1.98, -2.26, -1.98])
    assert months(solution["arc price"], 6) == pytest.approx([0, -0.72, -0.72, -0.72, -1, -0.72])
    assert months(solution["node price"], "Regional warehouse 2") == pytest.approx([0, 0, 0, 0, -1.72, 0])
    march = {i: solution["storage price"][i, "Mar"] for i in NODES if i != "Rail terminal"}
    # In March one more bike of storage capacity at a node saves 14 EUR, the holding
    # cost at local warehouse 4, less the holding cost at that node
    assert march == pytest.approx({i: -(14 - dn.c_h_node[i]) for i in march})
    assert months(solution["storage price"], "Plant 1") == pytest.approx([-4, -4, -9, -3, 0, 0])
    assert months(solution["storage price"], "Central warehouse") == pytest.approx([-1, -1, -6, 0, 0, 0])
    assert all(solution["arc price"][a, t] == 0 for a in range(13) if a not in (3, 6) for t in T)


@pytest.mark.parametrize("capacity, cost, rail", [
    (200, 1112018.47, [156, 200, 200, 200, 200, 200]),
    (150, 1112221.83, [150] * 6),
    (100, 1112498.03, [100] * 6),
    (50, 1112833.55, [50] * 6)])
def test_rail_capacity(capacity, cost, rail):
    arc_list = [dict(arc) for arc in ARCS]
    arc_list[dn.RAIL_ARC]["capacity"] = capacity
    solution = dn.solve(arc_list=arc_list)
    assert solution["cost"] == pytest.approx(cost)
    assert months(solution["flow"], dn.RAIL_ARC) == pytest.approx(rail)


def test_rail_capacity_below_which_there_is_no_solution():
    for capacity, solved in ((12, False), (13, True)):
        arc_list = [dict(arc) for arc in ARCS]
        arc_list[dn.RAIL_ARC]["capacity"] = capacity
        assert (dn.solve(arc_list=arc_list) is not None) == solved


@pytest.mark.parametrize("rate, cost, rail, road", [
    (0.004, 1111224.39, [176, 200, 200, 200, 200, 200], [0, 0, 0, 0, 20, 0]),
    (0.008, 1112792.99, [156, 200, 200, 200, 200, 200], [0, 0, 0, 0, 20, 0]),
    (0.010, 1113123.47, [0, 4, 10, 4, 70, 0], [84, 150, 150, 150, 150, 115]),
    (0.015, 1113267.03, [0, 0, 0, 4, 70, 0], [98, 150, 150, 150, 150, 115])])
def test_rail_rate(rate, cost, rail, road):
    arc_list = arcs({"Road": 0.010, "Rail": rate})
    solution = dn.solve(arc_list=arc_list)
    assert solution["cost"] == pytest.approx(cost)
    assert months(solution["flow"], dn.RAIL_ARC) == pytest.approx(rail)
    assert months(solution["flow"], 7) == pytest.approx(road)


def test_rail_rate_at_which_the_two_routes_cost_the_same():
    arc_list = arcs({"Road": 0.010, "Rail": 0.009})
    assert arc_list[dn.RAIL_ARC]["cost"] + arc_list[6]["cost"] == pytest.approx(arc_list[7]["cost"])
    assert dn.solve(arc_list=arc_list)["cost"] == pytest.approx(1113093.55)
    assert dn.only_plan(arc_list=arc_list) is False


@pytest.mark.parametrize("capacity, cost", [(300, 1111994.39), (280, 1112018.47), (250, 1112101.67)])
def test_node_capacity(capacity, cost):
    solution = dn.solve(node_capacity={"Regional warehouse 2": capacity})
    assert solution["cost"] == pytest.approx(cost)


def test_node_capacity_below_which_there_is_no_solution():
    assert dn.solve(node_capacity={"Regional warehouse 2": 222}) is None
    assert dn.solve(node_capacity={"Regional warehouse 2": 223}) is not None


def test_plans_without_a_constraint():
    # The sentences of §4 on what each constraint changes
    without_arcs = [dict(arc, capacity=10**5) for arc in ARCS]
    assert dn.solve(arc_list=without_arcs)["cost"] == pytest.approx(1111544.87)
    room = {i: (0 if i == "Rail terminal" else 10**5) if i not in F + ["Central warehouse"] else K_h_node[i]
            for i in NODES}
    solution = dn.solve(storage=room)
    assert solution["cost"] == pytest.approx(1111698.07)
    assert solution["stock"]["Regional warehouse 1", "Mar"] == pytest.approx(186)
    solution = dn.solve(backorders_end=None)
    assert solution["cost"] == pytest.approx(579685.16)
    assert sum(solution["backorders"][i, "Jun"] for i in LOCAL) == pytest.approx(2980)
    solution = dn.solve(capacity={f: {t: 10**5 for t in T} for f in F})
    assert solution["cost"] == pytest.approx(1078608.09)
    assert max(solution["flow"][a, t] for a in (0, 1) for t in T) == pytest.approx(300)
    solution = dn.solve(final=None)
    assert solution["cost"] == pytest.approx(1100151.97)
    assert all(solution["stock"][i, "Jun"] == 0 for i in NODES)
    assert dn.solve(node_capacity={})["flow"][7, "May"] + 260 == pytest.approx(294)


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
