"""Check that the package reproduces the numbers of capacity_scenarios.md (M4B),
that M4 is unchanged, and that the notebook of M4B runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from plants import capacity_scenarios as co  # noqa: E402
from plants import retailers as rt  # noqa: E402
from plants.data import (BASE_FORECAST, F, FORECAST_5, PRICE, RETAILERS, SHARE_M4, T, c_F, c_l, c_o,  # noqa: E402
                         c_u, o_max, u_max)

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "capacity_scenarios.ipynb"
PLANT_3 = "Plant 3"


def months(values, key):
    return [values[key, t] for t in T]


def lost(solution):
    return sum(solution["lost sales"].values())


def test_table1_and_2_data_of_m4b():
    assert [BASE_FORECAST[t] for t in T] == [200, 400, 350, 700, 700, 450]
    assert sum(BASE_FORECAST.values()) == 2800
    assert all(PRICE[t] == 700 for t in T)
    order = co.orders()
    assert all(abs(o - round(o)) < 1e-9 for o in order.values())
    assert months(order, "Retailer 1") == pytest.approx([28, 56, 49, 98, 98, 63])
    assert months(order, "Retailer 6") == pytest.approx([20, 40, 35, 70, 70, 45])
    assert (o_max, c_o, u_max, c_u) == ({"Plant 1": 25, "Plant 2": 20, "Plant 3": 0}, 100, 200, 12)
    assert c_F == {"Plant 1": 0, "Plant 2": 0, "Plant 3": 20000}
    # The data of M4 do not change: forecast 5 and the lost-sale cost of M4
    assert [FORECAST_5[t] for t in T] == [250, 500, 450, 900, 900, 550]
    assert c_l == {r: 700 for r in RETAILERS}
    assert sum(SHARE_M4.values()) == pytest.approx(1)


def test_m4b_with_the_data_of_m4_is_m4():
    m4b, m4 = co.solve(demand=FORECAST_5), rt.solve()
    assert m4b["cost"] == pytest.approx(1294204.84)
    for kind in ("assembly", "flow", "stock", "deliveries", "backorders", "lost sales"):
        assert m4b[kind] == pytest.approx(m4[kind], abs=1e-6)
    assert sum(m4b["overtime"].values()) == 0 and sum(m4b["rented"].values()) == 0


def test_tables4_and_5_plan_under_the_base_forecast():
    solution = co.solve()
    assert solution["cost"] == pytest.approx(949331.78)
    assert solution["margin"] == pytest.approx(1010668.22)
    assert solution["margin"] == pytest.approx(700 * 2800 - solution["cost"])
    assert {f: months(solution["assembly"], f) for f in F} == pytest.approx({
        "Plant 1": [250] * 6, "Plant 2": [190, 200, 200, 200, 200, 200], "Plant 3": [0, 0, 0, 0, 80, 30]})
    assert [100 * solution["capacity utilization"][f] for f in F] == pytest.approx(
        [100, 99.17, 12.22], abs=0.01)
    stock = solution["seasonal stock"]
    assert [stock["Plants"][t] for t in T] == pytest.approx([70, 70, 70, 70, 0, 30])
    assert [stock["Central warehouse"][t] for t in T] == pytest.approx([150, 150, 150, 100, 0, 0])
    assert [stock["Regional warehouses"][t] for t in T] == pytest.approx([50, 100, 120, 0, 0, 0])
    assert [stock["Local warehouses"][t] for t in T] == pytest.approx([0, 0, 80, 0, 0, 0])
    assert [stock["Total"][t] for t in T] == pytest.approx([270, 320, 420, 170, 0, 30])
    assert lost(solution) == 0
    assert co.only_plan() is True


@pytest.mark.parametrize("growth, cost, margin, plant_3, lost_sales", [
    (0.05, 1003847.02, 1054152.98, 26.7, 0), (0.10, 1059312.65, 1096687.35, 42.2, 0),
    (0.15, 1116024.03, 1137975.97, 57.8, 0), (0.20, 1177290.84, 1174709.16, 72.2, 10),
    (0.25, 1261580.31, 1188419.69, 77.5, 102.5), (0.30, 1347069.27, 1200930.73, 82.8, 195),
    (0.35, 1432942.63, 1213057.37, 88.1, 287.5), (0.40, 1519074.14, 1224925.86, 93.3, 380)])
def test_table6_plans_under_a_demand_growth(growth, cost, margin, plant_3, lost_sales):
    solution = co.solve(growth=growth)
    assert solution["cost"] == pytest.approx(cost)
    assert solution["margin"] == pytest.approx(margin)
    assert 100 * solution["capacity utilization"][PLANT_3] == pytest.approx(plant_3, abs=0.05)
    assert lost(solution) == pytest.approx(lost_sales)
    # Plants 1 and 2 assemble at their capacity in every month
    assert [solution["capacity utilization"][f] for f in F[:2]] == pytest.approx([1, 1])


def test_rented_storage_under_a_demand_growth_of_25_per_cent():
    solution = co.solve(growth=0.25, rented=u_max)
    assert solution["cost"] == pytest.approx(1233100.85)
    assert solution["margin"] == pytest.approx(1216899.15)
    assert 100 * solution["capacity utilization"][PLANT_3] == pytest.approx(88.9, abs=0.05)
    assert lost(solution) == 0
    assert [solution["rented"][t] for t in T] == pytest.approx([0, 0, 110, 0, 0, 0])
    assert co.only_plan(growth=0.25, rented=u_max) is True


@pytest.mark.parametrize("promotion_months, discount, growth, rented, margin, plant_3, lost_sales", [
    (["Jan", "Feb", "Mar"], 0.15, 0.51, 0, 1011205.85, 64.9, 0),
    (["Apr", "May"], 0.05, 0.14, 0, 1013286.16, 34.0, 0),
    (["Apr", "May"], 0.075, 0.17, 0, 995397.36, 38.7, 0),
    (["Apr", "May"], 0.075, 0.24, 0, 1012357.71, 48.5, 9.6),
    (["Apr", "May"], 0.10, 0.33, u_max, 1011392.50, 62.2, 2.2)])
def test_table7_plans_under_a_price_promotion(promotion_months, discount, growth, rented, margin,
                                              plant_3, lost_sales):
    data = {**co.promotion(promotion_months, discount=discount, growth=growth), "rented": rented}
    solution = co.solve(**data)
    assert solution["margin"] == pytest.approx(margin)
    assert 100 * solution["capacity utilization"][PLANT_3] == pytest.approx(plant_3, abs=0.05)
    assert lost(solution) == pytest.approx(lost_sales)
    # The price falls only in the months of the promotion
    assert [solution["price"][t] for t in T] == pytest.approx(
        [700 * (1 - discount) if t in promotion_months else 700 for t in T])


def test_promotion_of_january_to_march_delivers_every_order():
    data = co.promotion(["Jan", "Feb", "Mar"], discount=0.15, growth=0.51)
    solution = co.solve(**data)
    assert months(solution["assembly"], PLANT_3) == pytest.approx([0, 104.5, 150, 150, 150, 30])
    assert solution["seasonal stock"]["Total"]["Mar"] == pytest.approx(200)
    assert co.only_plan(**data) is True


@pytest.mark.parametrize("overtime, rented, cost, margin, lost_sales, overtime_bikes, rented_bikes", [
    (False, 0, 984056.63, 975943.37, 110, 0, 0), (True, 0, 952992.68, 1007007.32, 0, 110, 0),
    (False, u_max, 980740.88, 979259.12, 100, 0, 10), (True, u_max, 952378.68, 1007621.32, 0, 100, 30)])
def test_table8_plans_with_plant_3_closed(overtime, rented, cost, margin, lost_sales, overtime_bikes,
                                          rented_bikes):
    data = {"plant_3": co.CLOSED, "overtime": o_max if overtime else None, "rented": rented}
    solution = co.solve(**data)
    assert solution["cost"] == pytest.approx(cost)
    assert solution["margin"] == pytest.approx(margin)
    assert lost(solution) == pytest.approx(lost_sales)
    assert sum(solution["overtime"].values()) == pytest.approx(overtime_bikes)
    assert max(solution["rented"].values()) == pytest.approx(rented_bikes)
    assert solution["capacity utilization"][PLANT_3] == 0


def test_the_lost_sales_without_plant_3_fall_on_granada_and_alicante():
    solution = co.solve(plant_3=co.CLOSED)
    by_retailer = {r: sum(months(solution["lost sales"], r)) for r in RETAILERS}
    assert by_retailer["Retailer 6"] == pytest.approx(105)
    assert by_retailer["Retailer 3"] == pytest.approx(5)
    assert sum(by_retailer.values()) == pytest.approx(110)
    assert solution["lost sales share"]["Retailer 6"] == pytest.approx(0.375)


@pytest.mark.parametrize("growth, open_3, cost", [
    (0, 0, 952378.68), (0.10, 0, 1106506.49), (0.15, 0, 1205789.56), (0.18, 0, 1265709.11),
    (0.20, 1, 1293474.12)])
def test_plant_3_left_to_the_model(growth, open_3, cost):
    data = {"growth": growth, "plant_3": co.VARIABLE, "overtime": o_max, "rented": u_max, "fixed_cost": c_F}
    solution = co.solve(**data)
    assert solution["open"][PLANT_3] == open_3
    assert solution["cost"] == pytest.approx(cost)


def test_the_plan_with_plant_3_left_to_the_model_is_the_only_optimal_plan():
    assert co.only_plan(plant_3=co.VARIABLE, overtime=o_max, rented=u_max, fixed_cost=c_F) is True


def test_plans_without_a_constraint():
    # The sentences of §3 on what each new constraint changes
    room = {f: {t: 10 ** 5 for t in T} for f in F}
    solution = co.solve(capacity=room)
    assert solution["cost"] == pytest.approx(929020.48)
    assert months(solution["assembly"], "Plant 1") == pytest.approx([280, 300, 300, 300, 300, 320])
    assert sum(months(solution["assembly"], PLANT_3)) == 0
    solution = co.solve(plant_3=co.CLOSED, overtime={f: 10 ** 5 for f in F})
    assert solution["cost"] == pytest.approx(952429.68)
    assert solution["overtime"]["Plant 1", "May"] == pytest.approx(50)
    # more of the overtime at plant 1 than with the overtime limit, 75 bikes
    assert sum(months(solution["overtime"], "Plant 1")) == pytest.approx(90)
    # the limit of the rented storage is reached in the promotion of April and May with a discount of 10 %
    data = {**co.promotion(["Apr", "May"], discount=0.10, growth=0.33), "rented": u_max}
    solution = co.solve(**data)
    assert solution["rented"]["Mar"] == pytest.approx(200)
    assert solution["assembly"][PLANT_3, "Jan"] == 0
    assert solution["lost sales"]["Retailer 1", "May"] + solution["backorders"]["Retailer 1", "May"] == pytest.approx(22)
    from plants.data import CENTRAL, K_h_node_m4
    solution = co.solve(plant_3=co.CLOSED, rented=u_max, storage={**K_h_node_m4, CENTRAL: 10 ** 5})
    assert solution["cost"] == pytest.approx(979863.68)
    assert solution["stock"][CENTRAL, "Mar"] == pytest.approx(360)
    assert max(solution["rented"].values()) == 0
    data = {**co.promotion(["Apr", "May"], discount=0.10, growth=0.33), "rented": 10 ** 5}
    solution = co.solve(**data)
    assert solution["cost"] == pytest.approx(1140899.99)
    assert solution["rented"]["Mar"] == pytest.approx(222)
    assert lost(solution) == 0


def test_limits_of_the_growth_with_every_order_delivered():
    # §5.2 and §5.3: up to 17 % in April and May, with or without a growth in the other months
    for data in ({"growth": 0.18}, co.promotion(["Apr", "May"], discount=0.075, growth=0.18)):
        solution = co.solve(**data)
        assert lost(solution) == pytest.approx(1.2)
        assert solution["lost sales"]["Retailer 1", "May"] == pytest.approx(1.2)
        assert solution["backorders"]["Retailer 1", "May"] == pytest.approx(10.8)
    assert lost(co.solve(growth=0.17)) == 0
    # up to 71 % in January to March: with 72 %, 4 orders of May at Lleida are not delivered in May
    for discount in (0.05, 0.075, 0.10, 0.15):
        assert lost(co.solve(**co.promotion(["Jan", "Feb", "Mar"], discount=discount, growth=0.71))) == 0
        solution = co.solve(**co.promotion(["Jan", "Feb", "Mar"], discount=discount, growth=0.72))
        assert lost(solution) == pytest.approx(0.4)
        assert solution["lost sales"]["Retailer 1", "May"] == pytest.approx(0.4)
        assert solution["backorders"]["Retailer 1", "May"] == pytest.approx(3.6)
    order = co.orders(growth={t: 0.72 if t in ("Jan", "Feb", "Mar") else 0 for t in T})
    assert sum(order[r, t] for r in RETAILERS for t in T[:5]) == pytest.approx(3034)


def test_growths_that_reach_the_margin_under_the_base_forecast():
    reference = co.solve()["margin"]
    margin = lambda months, discount, growth: co.solve(  # noqa: E731
        **co.promotion(months, discount=discount, growth=growth))["margin"]
    assert margin(["Jan", "Feb", "Mar"], 0.05, 0.13) >= reference > margin(["Jan", "Feb", "Mar"], 0.05, 0.12)
    # A discount of 10 % in April and May reaches at most 988.725,30 EUR, with a growth of 35 %
    margins = {g: margin(["Apr", "May"], 0.10, g / 100) for g in range(81)}
    assert max(margins, key=margins.get) == 35
    assert margins[35] == pytest.approx(988725.30)
    assert margins[0] == pytest.approx(reference - 70 * 1400)
    assert co.solve(rented=u_max)["margin"] == pytest.approx(1010712.32)


def test_both_capacity_options_with_plant_3_closed():
    solution = co.solve(plant_3=co.CLOSED, overtime=o_max, rented=u_max)
    assert months(solution["overtime"], "Plant 1") == pytest.approx([0, 0, 20, 25, 25, 25])
    assert months(solution["overtime"], "Plant 2") == pytest.approx([0, 0, 0, 0, 0, 5])
    assert solution["assembly"]["Plant 2", "Jan"] == pytest.approx(200)
    solution = co.solve(plant_3=co.CLOSED, overtime=o_max)
    assert months(solution["overtime"], "Plant 1") == pytest.approx([0, 0, 0, 25, 25, 25])
    assert months(solution["overtime"], "Plant 2") == pytest.approx([0, 0, 0, 10, 20, 5])


@pytest.mark.parametrize("growth, rest, more", [(0.18, 115368.20, 334), (0.20, 132376.06, 390)])
def test_what_closing_plant_3_adds_to_the_rest_of_the_cost(growth, rest, more):
    data = {"growth": growth, "overtime": o_max, "rented": u_max, "fixed_cost": c_F}
    closed, opened = co.solve(plant_3=co.CLOSED, **data), co.solve(plant_3=co.OPEN, **data)
    assert closed["cost"] - (opened["cost"] - 6 * c_F[PLANT_3]) == pytest.approx(rest, abs=0.01)
    assert lost(closed) - lost(opened) == pytest.approx(more)
    assert lost(opened) == 0


def test_a_closed_plant_assembles_nothing():
    solution = co.solve(plant_3=co.CLOSED, overtime=o_max)
    assert months(solution["assembly"], PLANT_3) == pytest.approx([0] * 6)
    assert months(solution["overtime"], PLANT_3) == pytest.approx([0] * 6)


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=300, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
