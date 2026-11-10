"""Check that the package and the script reproduce the numbers of
expanded_network.md, and that the notebook of the expanded network runs from
start to end."""

import subprocess
import sys
from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import expanded_network as en  # noqa: E402
from plants.data import (LOCAL_EXP, NODE_CAPACITY_YEAR, PLACES_EXP, PLACES_M4, POPULATION,  # noqa: E402
                         RETAILER_NETWORK, RETAILERS_EXP, ROAD_KM_EXP, ROUTE_RETAILERS, WEEKLY_ORDERS, YEARLY_ORDERS)

CASE = Path(__file__).resolve().parents[1]
NOTEBOOK = CASE / "notebooks" / "expanded_network.ipynb"
SCRIPT = CASE / "expanded_network_solver.py"


def city(node):
    return PLACES_EXP[node][0]


def test_data_of_the_expanded_network():
    assert len(RETAILERS_EXP) == 46 and len(LOCAL_EXP) == 12 and len(en.SITES) == 8
    # Retailers 1 to 6 and local warehouses 1 to 4 keep the places and points of M4 and M3
    for node in [*RETAILERS_EXP[:6], *LOCAL_EXP[:4]]:
        assert PLACES_EXP[node][1:] == PLACES_M4[node][1:]
    # A retailer in the same city as a local warehouse is at the urban distance of 10 km
    assert sum(km == 10.0 for row in ROAD_KM_EXP.values() for km in row) == 10
    assert 0.0 not in [km for row in ROAD_KM_EXP.values() for km in row]
    # The twelve arcs of M4 keep their distances
    for origin, destination, _, km, _ in RETAILER_NETWORK:
        assert ROAD_KM_EXP[origin][RETAILERS_EXP.index(destination)] == km
    assert YEARLY_ORDERS["Retailer 26"] == 6290 and YEARLY_ORDERS["Retailer 30"] == 770
    assert sum(YEARLY_ORDERS.values()) == 77000 and sum(NODE_CAPACITY_YEAR.values()) == 86500
    assert WEEKLY_ORDERS == {"Retailer 1": 25, "Retailer 2": 31, "Retailer 7": 85, "Retailer 9": 24,
                             "Retailer 11": 54, "Retailer 12": 15}


def test_tables5_to_7_four_plans_of_the_assignment():
    cheapest = en.cheapest_plan()
    assert cheapest["cost"] == pytest.approx(61542.10)
    assert cheapest["over"] == ["Local warehouse 1", "Local warehouse 6", "Local warehouse 10"]
    assert [cheapest["load"][l] for l in cheapest["over"]] == [2700, 6680, 4510]
    rule = en.rule_plan()
    assert rule["cost"] == pytest.approx(81086.90) and not rule["over"]
    assert {city(r): city(rule["warehouse"][r]) for r in RETAILERS_EXP
            if rule["warehouse"][r] != cheapest["warehouse"][r]} == {
        "Girona": "Tarragona", "Marbella": "Seville", "Gijón": "Santiago de Compostela", "Vigo": "Badajoz",
        "Badajoz": "Seville"}
    model = en.assignment_plan()
    assert model["cost"] == pytest.approx(64544.30)
    assert {city(r): city(model["warehouse"][r]) for r in RETAILERS_EXP
            if model["warehouse"][r] != cheapest["warehouse"][r]} == {
        "Sabadell": "Tarragona", "Manresa": "Girona", "Jaén": "Seville", "Cuenca": "Valencia",
        "Burgos": "Alcalá de Henares", "León": "Valladolid"}
    assert [model["load"][l] for l in LOCAL_EXP] == pytest.approx(
        [2070, 12140, 6270, 8200, 10520, 5560, 11820, 5080, 6170, 3330, 3500, 2340])
    split = en.assignment_plan(split=True)
    assert split["cost"] == pytest.approx(61822.90)
    shared = {city(r): {city(l): round(100 * split["share"][l, r], 1) for l in LOCAL_EXP if split["share"][l, r] > 0}
              for r in RETAILERS_EXP if r not in split["warehouse"]}
    assert shared == {"Sabadell": {"Girona": 87.4, "Tarragona": 12.6}, "Jaén": {"Seville": 16.1, "Málaga": 83.9},
                      "Segovia": {"Alcalá de Henares": 41.6, "Valladolid": 58.4},
                      "León": {"Valladolid": 43.2, "Oviedo": 56.8}}
    assert rule["cost"] / model["cost"] - 1 == pytest.approx(0.256, abs=5e-4)
    assert 1 - split["cost"] / model["cost"] == pytest.approx(0.042, abs=5e-4)


def test_orders_of_the_retailers_of_m4():
    # Each retailer of M4 orders in the design year at least twice its orders of
    # January to June in M4 (retailers.md, Table 3)
    semester = dict(zip(RETAILERS_EXP[:6], [497, 781, 639, 568, 710, 355]))
    assert all(YEARLY_ORDERS[r] >= 2 * semester[r] for r in semester)
    # 1.280 is the lowest constant that does it; Sabadell sets it
    lower = {r: int(10 * round(1270 * (POPULATION[r] / 150000) ** 0.5 / 10)) for r in semester}
    assert [r for r in semester if lower[r] < 2 * semester[r]] == ["Retailer 2"]


def test_the_retailers_of_local_warehouse_2():
    model = en.assignment_plan()
    assert [r for r in RETAILERS_EXP if model["warehouse"][r] == "Local warehouse 2"] == ROUTE_RETAILERS


def test_moves_to_make_room():
    # Sentences of §3.2: the loads that each move avoids
    cheapest = en.cheapest_plan()
    assert cheapest["load"]["Local warehouse 2"] + YEARLY_ORDERS["Retailer 2"] == 13100
    assert cheapest["load"]["Local warehouse 8"] + YEARLY_ORDERS["Retailer 35"] == 6490
    assert cheapest["load"]["Local warehouse 7"] + YEARLY_ORDERS["Retailer 34"] == 12600
    model = en.assignment_plan()
    assert model["cost"] - cheapest["cost"] == pytest.approx(3002.20)
    # Every plan that keeps Burgos at Valladolid costs more
    model_, x, _ = en.build_assignment()
    model_ += x["Local warehouse 8", "Retailer 34"] == 1
    model_.solve(en._solver())
    assert model_.objective.value() > model["cost"] + 1


def test_the_optimal_plans_are_unique():
    assert en.only_assignment() is True
    assert en.only_assignment(split=True) is True
    assert en.only_covering() is True
    routes = en.candidate_routes()
    assert en.only_routes(routes) is True
    assert en.only_routes(routes, exactly_one=False) is True
    assert en.only_routes(en.short_list(routes)) is True


def test_table9_regional_warehouses():
    plan = en.covering_plan()
    assert plan["sites"] == ["Barcelona", "Valencia", "Seville", "Valladolid", "León"]
    assert plan["cost"] == pytest.approx(2220)
    assert {city(l): sites for l, sites in plan["reached by"].items() if len(sites) > 1} == {
        "Tarragona": ["Barcelona", "Valencia"], "Valladolid": ["Valladolid", "León"],
        "Bilbao": ["Valladolid", "León"], "Oviedo": ["Valladolid", "León"]}
    alone = {city(l) for l in LOCAL_EXP if sum(l in s for s in plan["sets"].values()) == 1}
    assert alone == {"Girona", "Murcia", "Badajoz", "Santiago de Compostela"}
    assert en.covering_plan(exactly_one=True) is None
    # With Zaragoza instead of Valladolid
    assert en.covering_plan(site_cost={**en.SITE_COST, "Valladolid": 10**4})["cost"] == pytest.approx(2250)


def test_tables12_and_13_weekly_routes():
    routes = en.candidate_routes()
    assert len(routes) == 19 and len(en.short_list(routes)) == 15
    by_number = {route["number"]: route for route in routes}
    assert [city(r) for r in by_number[16]["stops"]] == ["Sabadell", "Lleida", "Tarragona"]
    assert (by_number[16]["km"], by_number[16]["cost"]) == (354.2, 362.52)
    assert (by_number[4]["km"], by_number[4]["cost"]) == (20.0, 162.0)
    assert (by_number[15]["km"], by_number[15]["cost"]) == (518.2, 460.92)
    for exactly_one in (True, False):
        plan = en.route_plan(routes, exactly_one=exactly_one)
        assert [route["number"] for route in plan["routes"]] == [3, 15, 16]
        assert plan["cost"] == pytest.approx(1089.54) and plan["km"] == pytest.approx(1065.9)
    short = en.route_plan(en.short_list(routes))
    assert [route["number"] for route in short["routes"]] == [3, 4, 7, 15]
    assert short["cost"] == pytest.approx(1245.54)


def test_plans_without_a_constraint():
    # §3.1: without the node capacity, the plan of each retailer at its cheapest warehouse
    big = {l: 10**6 for l in LOCAL_EXP}
    assert en.assignment_plan(capacity=big)["cost"] == pytest.approx(en.cheapest_plan()["cost"])


def test_script_agrees_with_the_package():
    out = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, check=True, cwd=CASE).stdout
    for text in ["61.542,10", "81.086,90", "64.544,30", "61.822,90", "2.220 thousand", "no feasible solution",
                 "routes 3; 15; 16", "1.089,54", "routes 3; 4; 7; 15", "1.245,54", "77.000", "12,3 %"]:
        assert text in out
    assert "False" not in out


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
