"""Check that the script of M4B, Master Planning for Electric Bicycles: Optimization Model and Scenario Analysis, reproduces the numbers of
capacity_scenarios.md, and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

CASE = Path(__file__).resolve().parents[1] / "cases" / "production_plan"
SCRIPT = "capacity_scenarios_solver.py"


def load():
    spec = importlib.util.spec_from_file_location(Path(SCRIPT).stem, CASE / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("Orders in the six months: 2.800 bikes; capacity of the three plants: 3.600 bikes",
                 "Cost: 949.331,78 EUR; margin: 1.010.668,22 EUR; lost sales: 0 bikes",
                 "Capacity utilization: Plant 1 100,0 %; Plant 2 99,2 %; Plant 3 12,2 %",
                 "1.519.074,14",                       # cost under a growth of 40 % (Table 6)
                 "rented storage at the end of March 110 bikes",   # growth of 25 % with rented storage
                 "1.011.205,85",                       # margin of the promotion of January to March
                 "995.397,36",                         # margin of the promotion with a discount of 7,5 %
                 "952.378,68",                         # plant 3 closed with both capacity options
                 "plant 3 open; cost 1.293.474,12 EUR",
                 # growths found in steps of one percentage point (§5.2 and §5.3)
                 "every order is delivered up to a growth of 17 %; with 18 %, lost sales 1,2 bikes",
                 "Jan, Feb, Mar, discount 15,0 %: every order is delivered up to a growth of 71 %",
                 "Jan, Feb, Mar, discount 5,0 %: the margin first reaches the margin under the base forecast with a growth of 13 %",
                 "966.732,36 EUR with 17 %; highest margin 988.725,30 EUR, with a growth of 35 %",
                 "the margin under the base forecast with that rented storage, at a growth of 33 %",
                 # what closing plant 3 adds to the rest of the cost (§5.4)
                 "raises the rest of the cost by 115.368,20 EUR, 345,41 EUR on average for each of the 334,0 more lost sales",
                 "raises the rest of the cost by 132.376,06 EUR, 339,43 EUR on average for each of the 390,0 more lost sales"):
        assert text in out


def test_script_agrees_with_the_package():
    from plants import capacity_scenarios as co
    script = load()
    for data, options in (({}, {}),
                          ({"growth": 0.25, "rented": script.u_max},
                           {"growth": 0.25, "rented": script.u_max}),
                          ({"plant_3": "closed", "overtime": True, "rented": script.u_max},
                           {"plant_3": "closed", "overtime": co.o_max, "rented": script.u_max})):
        plan = script.solve_model(**data)
        package = co.solve(**options)
        assert plan["cost"] == pytest.approx(package["cost"])
        assert plan["margin"] == pytest.approx(package["margin"])
        for kind, key in (("p", "assembly"), ("o", "overtime"), ("x", "flow"), ("h", "stock"),
                          ("s", "deliveries"), ("b", "backorders"), ("l", "lost sales")):
            assert plan["values"][kind] == pytest.approx(package[key], abs=1e-6)
        assert plan["values"]["u"] == pytest.approx(package["rented"], abs=1e-6)
    # The script writes the same promotion as the package
    months, discount, growth = ["Apr", "May"], 0.075, 0.24
    price = {t: script.PRICE[t] * (1 - discount) if t in months else script.PRICE[t] for t in script.T}
    rise = {t: growth if t in months else 0.0 for t in script.T}
    plan = script.solve_model(growth=rise, price=price)
    package = co.solve(**co.promotion(months, discount=discount, growth=growth))
    assert plan["margin"] == pytest.approx(package["margin"]) == pytest.approx(1012357.71)
    # The script and the package read the same network and the same data of M4B
    assert [arc[5] for arc in script.ARCS] == [arc["cost"] for arc in co.ARCS_M4]
    assert script.D == co.BASE_FORECAST and script.PRICE == co.PRICE
    assert (script.o_max, script.c_o, script.u_max, script.c_u) == (co.o_max, co.c_o, co.u_max, co.c_u)
