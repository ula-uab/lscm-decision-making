"""Check that the script of M2, central warehouse, reproduces the numbers of
central_warehouse.md, and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1] / "cases" / "production_plan"
SCRIPT = "central_warehouse_solver.py"


def load():
    spec = importlib.util.spec_from_file_location(Path(SCRIPT).stem, CASE / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(name, values, width=40):
    """A row of the script output: the name, then one value per month."""
    return f"{name:<{width}}" + "".join(f"{v:>9.2f}" for v in values)


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("M1 (stock at the plants only) has a solution: no",
                 "Cost: 928480.00 EUR",
                 row("Backorders at the end of the month", [0, 60, 0, 0, 0, 0]),
                 row("Deliveries of the warehouse", [380, 840, 480, 440, 430, 230]),
                 row("Backorder balance", [390, 450, 390, 340, 340, 340]),
                 row("Storage capacity, warehouse", [-52, 0, 0, 0, 0, 0])):
        assert text in out


def test_script_agrees_with_the_package():
    from plants import central_warehouse as cw
    from plants.data import F, T
    script = load()
    cost, values, orders_price, storage_price, warehouse_price = script.solve_model()
    package = cw.solve()
    assert cost == package["cost"]
    for kind, key in (("p", "assembly"), ("x", "shipments"), ("h", "stock"), ("h_w", "warehouse stock"),
                      ("s", "served"), ("b", "owed")):
        assert values[kind] == package[key]
    assert orders_price == package["orders price"]
    assert storage_price == package["storage price"]
    assert warehouse_price == package["warehouse storage price"]
    assert script.solve_model(m1=True) is None
    assert set(F) == {f for f, _ in values["p"]} and set(T) == set(values["s"])
