"""Check that the script of M4, retailers, reproduces the numbers of retailers.md,
and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

CASE = Path(__file__).resolve().parents[1] / "cases" / "production_plan"
SCRIPT = "retailers_solver.py"


def load():
    spec = importlib.util.spec_from_file_location(Path(SCRIPT).stem, CASE / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def eu(x):
    """A number as the script writes it: European format, two decimals."""
    return f"{x:,.2f}".replace(",", " ").replace(".", ",").replace(" ", ".")


def row(name, values, width=58):
    """A row of the script output: the name, then one value per month."""
    return f"{name:<{width}}" + "".join(f"{eu(v):>10}" for v in values)


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("M3 (orders at the local warehouses) has a solution with the higher late demand peak: no",
                 "Cost: 1.294.204,84 EUR",
                 "Lost sales, all retailers: 140,00 of 3.550,00 orders",
                 row("Lost sales, Retailer 6 (Granada)", [0, 0, 0, 0, 54, 51]),
                 row("Arc capacity, 22. Local warehouse 4 -> Retailer 5", [0, 0, 0, -2.11, -2.11, 0]),
                 "Lost sales  Retailer 6                                          Jun    -0,5 x  700,00   -350,000",
                 "Change in the cost of the plan: -296,165 EUR"):
        assert text in out


def test_script_agrees_with_the_package():
    from plants import retailers as rt
    script = load()
    cost, values, prices = script.solve_model(script.NODES + script.RETAILERS, script.ARCS_M4, script.SHARE)
    package = rt.solve()
    assert cost == pytest.approx(package["cost"])
    for kind, key in (("p", "assembly"), ("x", "flow"), ("h", "stock"), ("s", "deliveries"), ("b", "backorders"),
                      ("l", "lost sales")):
        assert values[kind] == pytest.approx(package[key], abs=1e-6)
    assert prices["arc"] == pytest.approx(package["arc price"], abs=1e-6)
    assert [arc[5] for arc in script.ARCS_M4] == [arc["cost"] for arc in rt.ARCS_M4]


def test_script_table10_agrees_with_the_package():
    from plants import retailers as rt
    script = load()
    _, values, _ = script.solve_model(script.NODES + script.RETAILERS, script.ARCS_M4, script.SHARE)
    _, new, _ = script.solve_model(script.NODES + script.RETAILERS, script.ARCS_M4, script.SHARE,
                                   extra_storage={("Local warehouse 4", "Mar"): 1})
    rows = script.breakdown(values, new)
    package = rt.storage_price_breakdown("Local warehouse 4", "Mar")
    assert [(r[0], r[2], r[3], r[5]) for r in rows] == pytest.approx(
        [(r["term"], r["month"], r["change"], r["cost"]) for r in package])
    assert sum(r[5] for r in rows) == pytest.approx(-296.165, abs=1e-6)
