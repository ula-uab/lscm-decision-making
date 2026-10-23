"""Check that the script of M3, distribution network, reproduces the numbers of
distribution_network.md, and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1] / "cases" / "production_plan"
SCRIPT = "distribution_network_solver.py"


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
    for text in ("M2 (plants and central warehouse only) has a solution with forecast 4: no",
                 "Cost: 1.112.018,47 EUR",
                 row("7. Rail terminal -> Regional warehouse 2", [156, 200, 200, 200, 200, 200]),
                 row("Node capacity, Regional warehouse 2", [0, 0, 0, 0, -1.72, 0]),
                 "Deliveries of each local warehouse equal its orders (Table 4) every month: yes"):
        assert text in out


def test_script_agrees_with_the_package():
    from plants import distribution_network as dn
    from plants.data import NODES
    script = load()
    cost, values, prices = script.solve_model(script.NODES, script.ARCS, script.SHARE, script.K_h)
    package = dn.solve()
    assert cost == package["cost"] and script.NODES == NODES
    for kind, key in (("p", "assembly"), ("x", "flow"), ("h", "stock"), ("s", "deliveries"), ("b", "backorders")):
        assert values[kind] == package[key]
    assert prices["arc"] == package["arc price"] and prices["node"] == package["node price"]
    assert prices["storage"] == package["storage price"]
    assert [arc[5] for arc in script.ARCS] == [arc["cost"] for arc in dn.ARCS]
