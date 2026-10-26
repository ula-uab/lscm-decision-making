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
CAMPAIGN = ("RIX–HEL", "Economy FLEX")


def by_trip(plan):
    """A plan as one list per trip: Business, FLEX, BASIC."""
    return [[plan[trip, fare] for trip_, fare in P if trip_ == trip] for trip in TRIPS]


def test_table3_optimal_plan():
    solution = m.solve()
    assert solution["revenue"] == pytest.approx(41235)
    assert by_trip(solution["plan"]) == [[16, 60, 105], [6, 40, 60], [6, 20, 2]]
    assert solution["seats"] == {FIRST: 220, SECOND: 140}


def test_the_optimal_plan_is_unique():
    for low, high in m.plan_bounds().values():
        assert low == pytest.approx(high, abs=1e-6)


def test_table4_binding_constraints_and_slack():
    solution = m.solve()
    assert solution["spare seats"] == {FIRST: 0, SECOND: 0}
    assert {p: v for p, v in solution["unsold demand"].items() if v} == {
        ("BCN–RIX", "Economy BASIC"): 55, ("BCN–HEL", "Economy BASIC"): 78}


def test_a_third_connecting_basic_ticket_costs_ten_euros():
    # §2: the plan sells 2 BCN–HEL BASIC tickets of the 80 of its demand. Three seats
    # BCN–HEL forced into the plan at 110 €, the price of that fare, are the two
    # tickets it already sells and one more: that one takes a seat from a BCN–RIX
    # BASIC ticket (75 €) and a seat from a RIX–HEL BASIC ticket (45 €)
    assert m.offer(2, 110)["change"] == pytest.approx(0)
    third = m.offer(3, 110)
    assert third["change"] == pytest.approx(-10)
    assert m.changed_tickets(third["base"]["plan"], third["new"]["plan"]) == {
        ("BCN–RIX", "Economy BASIC"): (105, 104), ("RIX–HEL", "Economy BASIC"): (60, 59),
        ("BCN–HEL", "Economy BASIC"): (2, 0)}


def test_table5_bid_prices_are_the_change_with_one_seat_more_and_one_less():
    solution = m.solve()
    assert solution["bid price"] == {FIRST: pytest.approx(75), SECOND: pytest.approx(35)}
    for flight, bid in ((FIRST, 75), (SECOND, 35)):
        assert m.change_capacity(flight, 1) == pytest.approx(bid)
        assert m.change_capacity(flight, -1) == pytest.approx(-bid)


def test_table6_products_whose_tickets_change_with_one_seat():
    rows = {flight: [(row["product"], row["less"], row["plan"], row["more"], row["change"])
                     for row in m.seat_change(flight)] for flight in (FIRST, SECOND)}
    assert rows[FIRST] == [(("BCN–RIX", "Economy BASIC"), 104, 105, 106, 75)]
    assert rows[SECOND] == [(("BCN–HEL", "Economy BASIC"), 1, 2, 3, 110),
                            (("BCN–RIX", "Economy BASIC"), 106, 105, 104, -75)]
    # With one seat more, the changes add up to the bid price of the flight
    bid = m.solve()["bid price"]
    for flight in (FIRST, SECOND):
        assert sum(row["change"] for row in m.seat_change(flight)) == pytest.approx(bid[flight])


def test_table7_shadow_price_of_the_demand_is_price_minus_bid_price():
    solution = m.solve()
    prices = [solution["demand price"][p] for p in P]
    assert prices == pytest.approx([307.5, 105, 0, 147.5, 65, 10, 355, 120, 0])
    for p in P:
        assert solution["demand price"][p] == pytest.approx(m.r[p] - m.product_bid_price(p, solution["bid price"]))
    assert m.product_bid_price(("BCN–HEL", "Business"), solution["bid price"]) == pytest.approx(165)


def test_table8_ranges_of_the_bid_prices():
    assert m.validity_range("seats", FIRST) == (115, 275)
    assert m.validity_range("seats", SECOND) == (138, 218)


def test_table9_offer_of_a_tour_operator():
    assert m.offer(10, 100)["estimate"] == pytest.approx(-100)
    assert m.offer(10, 100)["change"] == pytest.approx(-180)
    assert m.offer(10, 120)["estimate"] == pytest.approx(100)
    assert m.offer(10, 120)["change"] == pytest.approx(20)
    assert [m.offer(n, 120)["change"] for n in (1, 2, 3)] == pytest.approx([10, 20, 20])


def test_table10_ranges_of_the_demand():
    # The demand of the two Business fares of the trips that use RIX → HEL holds up to
    # 6 + 2 / 1.5 tickets, where the 2 seats of the connecting BASIC tickets of the
    # plan are used up: a Business ticket takes 1.5 seats
    business_end = 6 + 2 / 1.5
    expected = [(0, 86), (5, 165), (105, None),
                (0, business_end), (0, 42), (0, 62),
                (0, business_end), (0, 22), (2, None)]
    for p, (low, high) in zip(P, expected):
        got_low, got_high = m.validity_range("demand", p)
        assert got_low == pytest.approx(low)
        if high is None:
            assert got_high is None
        else:
            assert got_high == pytest.approx(high, abs=1e-3)


def test_table11_campaign_that_raises_the_demand_of_a_fare():
    campaign = m.demand_change(CAMPAIGN, 50, 600)
    assert campaign["shadow price"] == pytest.approx(65)
    assert campaign["range"] == (0, 42) and not campaign["inside"]
    assert campaign["estimate"] == pytest.approx(650) and campaign["net estimate"] == pytest.approx(50)
    assert campaign["new"]["revenue"] == pytest.approx(41805)
    assert campaign["change"] == pytest.approx(570) and campaign["net"] == pytest.approx(-30)
    assert by_trip(campaign["new"]["plan"]) == [[16, 60, 107], [6, 50, 52], [6, 20, 0]]
    assert campaign["new"]["bid price"] == {FIRST: pytest.approx(75), SECOND: pytest.approx(45)}
    assert campaign["changed"] == {("BCN–RIX", "Economy BASIC"): (105, 107),
                                  ("RIX–HEL", "Economy FLEX"): (40, 50),
                                  ("RIX–HEL", "Economy BASIC"): (60, 52),
                                  ("BCN–HEL", "Economy BASIC"): (2, 0)}
    # Inside the range each ticket is worth 65 €, and 55 € from the 43rd on
    changes = [m.demand_change(CAMPAIGN, D[CAMPAIGN] + extra)["change"] for extra in (1, 2, 3, 5, 10)]
    assert changes == pytest.approx([65, 130, 185, 295, 570])


def test_one_source_of_data():
    # The model, the tables and the figures read the same demand and seats of the aircraft
    assert m.D is D and m.C is C


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
