"""Check that the script of the production plan case reproduces the numbers of
production_plan.md, and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1] / "cases" / "production_plan"
SCRIPT = "production_plan_solver.py"


def load():
    spec = importlib.util.spec_from_file_location(Path(SCRIPT).stem, CASE / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("Optimum: p1 = 250.00, p2 = 130.00, cost 121700.00 EUR",
                 "Capacity of plant 1              250.00                   -30.00      180.00    380.00",
                 "Demand                           380.00                   340.00      250.00    450.00",
                 "Cost: 713800.00 EUR",
                 "The model has a solution: no",
                 "Capacity short: Apr 50 bikes, May 20 bikes",
                 "Jan 220, Feb 270, Mar 180 (670 in all)"):
        assert text in out


def test_script_agrees_with_the_package():
    from plants import model as m
    from plants.data import F, FORECASTS, K, T
    script = load()
    cost, plan, demand_price, capacity_price, reduced = script.solve_model(F, T, FORECASTS["Forecast 1"], K)
    package = m.solve(demand=FORECASTS["Forecast 1"])
    assert cost == package["cost"] and plan == package["plan"]
    assert demand_price == package["demand price"] and reduced == package["reduced cost"]
    assert capacity_price == package["capacity price"]
    assert script.solve_model(F, T, FORECASTS["Forecast 2"], K) is None
