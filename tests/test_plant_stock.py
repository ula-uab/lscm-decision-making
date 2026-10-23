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


def row(name, values, width=34):
    """A row of the script output: the name, then one value per month."""
    return f"{name:<{width}}" + "".join(f"{eu(v):>9}" for v in values)


def eu(x):
    """A number as the script writes it: European format, two decimals."""
    return f"{x:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("Demand above the capacity of plants 1 and 2: Apr 200 bikes; May 170 bikes",
                 "Cost: 858.460,00 EUR",
                 "Cost: 848.700,00 EUR",
                 row("With the required ending stock", [370, 375, 380, 385, 390, 340]),
                 row("Without the required ending stock", [370, 375, 380, 385, 390, 310]),
                 "Months with the same plan: Jan, Feb, Mar, Apr, May",
                 "Cost: 361.860,00 EUR",
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
