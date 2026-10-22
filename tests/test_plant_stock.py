"""Check that the script of M1, stock at the plants, reproduces the numbers of
plant_stock.md, and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1] / "cases" / "production_plan"
SCRIPT = "plant_stock_solver.py"


def load():
    spec = importlib.util.spec_from_file_location(Path(SCRIPT).stem, CASE / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("Plants 1 and 2 short: Apr 200 bikes, May 170 bikes",
                 "Cost: 858460.00 EUR",
                 "Cost: 848700.00 EUR",
                 "With the final-stock target          370.00   375.00   380.00   385.00   390.00   340.00",
                 "Without the final-stock target       370.00   375.00   380.00   385.00   390.00   310.00",
                 "Months with the same plan: Jan, Feb, Mar, Apr, May",
                 "Cost: 361860.00 EUR",
                 "The plan from April to June has a solution: no"):
        assert text in out


def test_script_agrees_with_the_package():
    from plants import plant_stock as ps
    from plants.data import T, h_0, h_end
    script = load()
    for months, final in ((T, h_end), (T, None), (T[:3], h_end)):
        cost, assembled, shipped, stock, price = script.solve_model(months, h_0, final)
        package = ps.solve(months=months, final=final)
        assert cost == package["cost"] and assembled == package["assembly"]
        assert shipped == package["shipments"] and stock == package["stock"]
        assert price == package["demand price"]
    assert script.solve_model(T[3:], h_end, h_end) is None
