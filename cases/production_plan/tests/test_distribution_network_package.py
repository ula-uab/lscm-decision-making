"""Check that the package reproduces the numbers of distribution_network.md (M3),
and that the notebook of M3 runs from start to end."""

import re
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import distribution_network as dn  # noqa: E402
from plants.data import ARCS, F, FORECAST_4, FORECASTS, K_h_node, LOCAL, NODES, SHARE, T  # noqa: E402

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
    assert list(FORECASTS) == ["Demand below capacity", "Seasonal demand peak"]


def test_m2_has_no_solution_with_forecast_4():
    assert dn.m2_has_no_solution()
    # 340 bikes assembled before April and the 30 of the required final stock of the
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


@pytest.mark.parametrize("capacity, cost, stock_april, delivered_may, pending_may", [
    (300, 1111994.39, 0, 294, 0),
    (280, 1112018.47, 14, 294, 0),
    (250, 1112101.67, 44, 294, 0),
    (240, 1112668.47, 40, 280, 14),
    (230, 1113471.27, 30, 260, 34),
    (223, 1114045.43, 23, 246, 48)])
def test_node_capacity(capacity, cost, stock_april, delivered_may, pending_may):
    # §6.4: the stock of regional warehouse 2 at the end of April, and the bikes
    # delivered to Seville in May and its orders pending at the end of May
    solution = dn.solve(node_capacity={"Regional warehouse 2": capacity})
    assert solution["cost"] == pytest.approx(cost)
    assert solution["stock"]["Regional warehouse 2", "Apr"] == pytest.approx(stock_april)
    assert solution["deliveries"]["Local warehouse 4", "May"] == pytest.approx(delivered_may)
    assert solution["backorders"]["Local warehouse 4", "May"] == pytest.approx(pending_may)


def test_node_capacity_ranges():
    # §6.4: never full from 294 up; full in May from 293; orders of Seville pending
    # from 246 down
    def solved(capacity):
        return dn.solve(node_capacity={"Regional warehouse 2": capacity})
    assert solved(294)["cost"] == pytest.approx(solved(10**5)["cost"])
    assert solved(293)["cost"] > solved(294)["cost"] + 1
    assert solved(247)["backorders"]["Local warehouse 4", "May"] == pytest.approx(0)
    assert solved(246)["backorders"]["Local warehouse 4", "May"] > 0


def test_node_capacity_below_which_there_is_no_solution():
    assert dn.solve(node_capacity={"Regional warehouse 2": 222}) is None
    assert dn.solve(node_capacity={"Regional warehouse 2": 220}) is None
    assert dn.solve(node_capacity={"Regional warehouse 2": 223}) is not None


def test_node_capacity_figures():
    # The routes to regional warehouse 2 with its stock, and to Valencia without it;
    # then Seville: orders, deliveries and pending orders
    solution = dn.solve(node_capacity={"Regional warehouse 2": 240})
    routes = dn._route_figure(solution, {"Regional warehouse 2": 240})
    getafe, valencia = (b.args[0]["visible"] for b in routes.layout.updatemenus[0].buttons)
    stock = [k for k, t in enumerate(routes.data) if t.name and t.name.startswith("stock of regional warehouse 2")]
    assert len(stock) == 1 and getafe[stock[0]] and not valencia[stock[0]]
    seville = dn._seville_figure(solution)
    assert [t.name for t in seville.data] == ["orders", "delivered", "pending at the end of the month"]
    assert list(seville.data[2].y) == pytest.approx([0, 0, 0, 0, 14, 0])


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


@pytest.mark.parametrize("month, cost, supply_nodes", [
    ("Jan", 2396.76, ["Plant 1", "Plant 2"]),
    ("Feb", 3686.68, ["Plant 1", "Plant 2"]),
    ("Mar", 4408.30, ["Plant 1", "Plant 2", "Plant 3"]),
    ("Apr", 5508.58, ["Plant 1", "Plant 2", "Plant 3", "Central warehouse", "Regional warehouse 1",
                      "Regional warehouse 2"]),
    ("May", 6736.40, ["Plant 1", "Plant 2", "Plant 3", "Central warehouse", "Regional warehouse 2"]),
    ("Jun", 4103.75, ["Plant 1", "Plant 2", "Plant 3"])])
def test_table10_minimum_cost_flow_problem_of_each_month(month, cost, supply_nodes):
    # §7.1: the problem of each month gives the transport cost and the flows of M3 in that month
    problem = dn.month_problem(month)
    assert problem["cost"] == pytest.approx(cost)
    assert problem["m3 cost"] == pytest.approx(cost)
    assert [problem["flow"][a] for a in range(13)] == pytest.approx([problem["m3 flow"][a] for a in range(13)])
    assert [i for i in NODES if problem["kind"][i] == dn.SUPPLY_NODE] == supply_nodes
    assert sum(problem["supply"].values()) == pytest.approx(0)


def test_net_supply_in_january_and_may():
    # §7.1: the central warehouse is a demand node in January; in May it and regional
    # warehouse 2 put into the network the 136 and 14 bikes they held at the end of April
    january, may = dn.month_problem("Jan"), dn.month_problem("May")
    assert january["supply"]["Central warehouse"] == pytest.approx(-150)
    assert january["kind"]["Plant 3"] == dn.TRANSHIPMENT_NODE
    assert may["supply"]["Central warehouse"] == pytest.approx(136)
    assert may["supply"]["Regional warehouse 2"] == pytest.approx(14)


@pytest.mark.parametrize("month, node, moves, arrows, supply", [
    ("Jan", "Plant 1", {"assembled": 250, "to stock": 20}, {("250", "down", "solid")}, 230),
    ("Jan", "Central warehouse", {"to stock": 150}, {("150", "up", "dashed")}, -150),
    ("Feb", "Central warehouse", {}, set(), 0),
    ("Mar", "Central warehouse", {}, set(), 0),
    ("Mar", "Local warehouse 1", {"delivered": 60, "to stock": 20}, {("60", "up", "solid"), ("20", "up", "dashed")}, -80),
    ("Apr", "Central warehouse", {"from stock": 14}, {("14", "down", "dashed")}, 14),
    ("Apr", "Regional warehouse 1", {"from stock": 60}, {("60", "down", "dashed")}, 60),
    ("Apr", "Regional warehouse 2", {"from stock": 46}, {("46", "down", "dashed")}, 46),
    ("Apr", "Local warehouse 1", {"from stock": 20, "delivered": 120}, {("20", "down", "dashed"), ("120", "up", "solid")},
     -100),
    ("May", "Plant 1", {"assembled": 250, "from stock": 40}, {("250", "down", "solid"), ("40", "down", "dashed")}, 290),
    ("May", "Regional warehouse 2", {"from stock": 14}, {("14", "down", "dashed")}, 14)])
def test_arrows_of_the_nodes(month, node, moves, arrows, supply):
    # The arrows of a node in the network of section 5 of the notebook: pointing down
    # what it puts into the network, pointing up what it takes out of it; solid what a
    # plant assembles or a local warehouse delivers, dashed stock. A plant has no
    # arrow of what it puts into its stock
    p = dn.month_problem(month)
    assert {m: v for m, v in p["moves"][node].items() if v} == pytest.approx(moves)
    assert p["supply"][node] == pytest.approx(supply)
    drawn = {(a["text"], "down" if a["head"][1] > a["tail"][1] else "up", "dashed" if a["dash"] else "solid")
             for a in dn.move_arrows(p["moves"]) if a["node"] == node}
    assert drawn == arrows


def test_moves_give_the_net_supply():
    # In every node and month, with the terms of its kind (no "assembled" at a
    # warehouse): assembled + from stock - delivered - to stock
    for t in T:
        p = dn.month_problem(t)
        for i in NODES:
            m = p["moves"][i]
            assert ("assembled" in m) == (i in F) and ("delivered" in m) == (i in LOCAL)
            assert m.get("assembled", 0) + m.get("from stock", 0) - m.get("delivered", 0) - m.get("to stock", 0) == \
                pytest.approx(p["supply"][i])


def test_arc_flow_figure():
    # The flow on an arc in each month, red where its arc capacity is full: the
    # rail arc (arc 6) never; arc 7, from the rail terminal, from February to June
    solution = dn.solve()
    rail = dn.arc_flow_figure(solution, dn.RAIL_ARC).data[0]
    assert list(rail.y) == pytest.approx([156, 200, 200, 200, 200, 200])
    assert dn.interactive.FULL not in rail.marker.color
    terminal = dn.arc_flow_figure(solution, dn.RAIL_ARC + 1).data[0]
    assert [colour == dn.interactive.FULL for colour in terminal.marker.color] == [False] + [True] * 5


def test_arc_flow_dropdown():
    # One figure with the 13 arcs, the rail arc shown first; each option of the
    # dropdown shows its arc only, with its title and its arc capacity
    fig = dn.arc_flow_selector(dn.solve())
    menu = fig.layout.updatemenus[0]
    assert len(fig.data) == len(menu.buttons) == 13
    assert [trace.visible for trace in fig.data] == [a == dn.RAIL_ARC for a in range(13)]
    assert menu.buttons[dn.RAIL_ARC].label == "6. Central warehouse → Rail terminal (rail)"
    visible, layout = menu.buttons[dn.RAIL_ARC + 1].args
    assert visible["visible"] == [a == dn.RAIL_ARC + 1 for a in range(13)]
    assert layout["title.text"].startswith("Flow on arc 7 (Rail terminal → Regional warehouse 2")
    assert layout["shapes"][0].y0 == 200


def test_interactive_figures():
    # The network has one option per month, May first; in May the full capacities
    # are arcs 4 and 7 and the node capacity of regional warehouse 2
    solution = dn.solve()
    menu = dn._flow_network(solution).layout.updatemenus[0]
    assert [b.label for b in menu.buttons] == T and menu.active == T.index("May")
    prices = dn._prices_figure(solution)
    may = prices.layout.updatemenus[0].buttons[T.index("May")].args[1]
    assert list(may["yaxis.ticktext"]) == ["Arc 4", "Arc 7", "Node capacity, Regional warehouse 2"]
    assert [b.label for b in dn._assembly_figure(solution).layout.updatemenus[0].buttons] == [*F, "All plants"]


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()


def test_notebook_runs_with_the_tables():
    # Every cell with the box show_tables, run with it ticked
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "code":
            cell.source = re.sub(r"^show_tables = \w+", "show_tables = True", cell.source, flags=re.MULTILINE)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
