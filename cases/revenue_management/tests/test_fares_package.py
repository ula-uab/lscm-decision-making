"""Check that the package of the notebook reproduces the numbers of
revenue_management.md, and that the notebook runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from fares import model as m  # noqa: E402
from fares.data import C, D, P, TRIPS  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "revenue_management.ipynb"
FIRST, SECOND = "BCN → RIX", "RIX → HEL"


def by_trip(plan):
    """A plan as one list per trip: Business, FLEX, BASIC."""
    return [[plan[trip, fare] for trip_, fare in P if trip_ == trip] for trip in TRIPS]


def test_table3_rule_highest_fare_first():
    rule = m.highest_fare_first()
    assert rule["revenue"] == pytest.approx(39465)
    assert by_trip(rule["plan"]) == [[16, 60, 27], [6, 22, 0], [6, 20, 80]]
    assert rule["seats"] == {FIRST: 220, SECOND: 140}


def test_table4_optimal_plan_and_difference_with_the_rule():
    solution = m.solve()
    assert solution["revenue"] == pytest.approx(41235)
    assert by_trip(solution["plan"]) == [[16, 60, 105], [6, 40, 60], [6, 20, 2]]
    assert solution["seats"] == {FIRST: 220, SECOND: 140}
    diff = m.difference(m.highest_fare_first()["plan"], solution["plan"])
    assert diff == {("BCN–HEL", "Economy BASIC"): (78, 8580), ("BCN–RIX", "Economy BASIC"): (-78, -5850),
                    ("RIX–HEL", "Economy BASIC"): (-60, -2700), ("RIX–HEL", "Economy FLEX"): (-18, -1800)}
    assert sum(v for _, v in diff.values()) == pytest.approx(-1770)


def test_the_optimal_plan_is_unique():
    for low, high in m.plan_bounds().values():
        assert low == pytest.approx(high, abs=1e-6)


def test_table5_binding_constraints_and_slack():
    solution = m.solve()
    assert solution["spare seats"] == {FIRST: 0, SECOND: 0}
    assert {p: v for p, v in solution["unsold demand"].items() if v} == {
        ("BCN–RIX", "Economy BASIC"): 55, ("BCN–HEL", "Economy BASIC"): 78}


def test_table6_bid_prices_are_the_change_with_one_seat_more_and_one_less():
    solution = m.solve()
    assert solution["bid price"] == {FIRST: pytest.approx(75), SECOND: pytest.approx(35)}
    for flight, bid in ((FIRST, 75), (SECOND, 35)):
        assert m.change_capacity(flight, 1) == pytest.approx(bid)
        assert m.change_capacity(flight, -1) == pytest.approx(-bid)



def test_table7_products_whose_tickets_change_with_one_seat():
    rows = {flight: [(row["product"], row["less"], row["plan"], row["more"], row["change"])
                     for row in m.seat_change(flight)] for flight in (FIRST, SECOND)}
    assert rows[FIRST] == [(("BCN–RIX", "Economy BASIC"), 104, 105, 106, 75)]
    assert rows[SECOND] == [(("BCN–HEL", "Economy BASIC"), 1, 2, 3, 110),
                            (("BCN–RIX", "Economy BASIC"), 106, 105, 104, -75)]
    # With one seat more, the changes add up to the bid price of the flight
    bid = m.solve()["bid price"]
    for flight in (FIRST, SECOND):
        assert sum(row["change"] for row in m.seat_change(flight)) == pytest.approx(bid[flight])

def test_table8_shadow_price_of_the_demand_is_price_minus_bid_price():
    solution = m.solve()
    prices = [solution["demand price"][p] for p in P]
    assert prices == pytest.approx([307.5, 105, 0, 147.5, 65, 10, 355, 120, 0])
    for p in P:
        assert solution["demand price"][p] == pytest.approx(m.r[p] - m.product_bid_price(p, solution["bid price"]))
    assert m.product_bid_price(("BCN–HEL", "Business"), solution["bid price"]) == pytest.approx(165)


def test_table9_ranges_of_the_bid_prices():
    assert m.validity_range(FIRST) == (115, 275)
    assert m.validity_range(SECOND) == (138, 218)


def test_table10_offer_of_a_tour_operator():
    assert m.offer(10, 100)["estimate"] == pytest.approx(-100)
    assert m.offer(10, 100)["change"] == pytest.approx(-180)
    assert m.offer(10, 120)["estimate"] == pytest.approx(100)
    assert m.offer(10, 120)["change"] == pytest.approx(20)
    assert [m.offer(n, 120)["change"] for n in (1, 2, 3)] == pytest.approx([10, 20, 20])


def test_table11_another_aircraft_on_the_second_flight():
    larger = m.other_aircraft(SECOND, 180, 1200)
    assert larger["new"]["revenue"] == pytest.approx(42635)
    assert larger["change"] == pytest.approx(1400) and larger["estimate"] == pytest.approx(1400)
    assert larger["inside"] and larger["net"] == pytest.approx(200)
    assert by_trip(larger["new"]["plan"]) == [[16, 60, 65], [6, 40, 60], [6, 20, 42]]
    smaller = m.other_aircraft(SECOND, 120, -800)
    assert smaller["new"]["revenue"] == pytest.approx(40355)
    assert smaller["change"] == pytest.approx(-880) and smaller["estimate"] == pytest.approx(-700)
    assert not smaller["inside"]
    assert smaller["net"] == pytest.approx(-80) and smaller["net estimate"] == pytest.approx(100)
    assert by_trip(smaller["new"]["plan"]) == [[16, 60, 107], [6, 40, 42], [6, 20, 0]]


def test_one_source_of_data():
    # The model, the tables and the figures read the same demand and capacity
    assert m.D is D and m.C is C


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
