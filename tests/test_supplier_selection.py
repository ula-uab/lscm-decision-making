"""Check that the three scripts of the supplier selection case reproduce the
numbers of supplier_selection.md, and that they agree with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

CASE = Path(__file__).resolve().parents[1] / "cases" / "supplier_selection"
SCRIPTS = ["supplier_selection_rule.py", "supplier_selection_local_search.py",
           "supplier_selection_solver.py"]


def load(script):
    spec = importlib.util.spec_from_file_location(Path(script).stem, CASE / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(script):
    return subprocess.run([sys.executable, script], cwd=CASE, capture_output=True, text=True,
                          check=True).stdout


def table_5(output):
    """The lines of Table 5, the buyer's rule, which the three scripts print."""
    start = output.index("Table 5.")
    return output[start:output.index("kEUR/year\n", start)]


@pytest.fixture(scope="module")
def outputs():
    return {script: run(script) for script in SCRIPTS}


def test_the_three_scripts_print_the_same_buyer_rule(outputs):
    tables = {table_5(out) for out in outputs.values()}
    assert len(tables) == 1
    assert "Purchases 2430.00 + fixed costs 200.00 = 2630.00" in tables.pop()


def test_rule_script(outputs):
    out = outputs["supplier_selection_rule.py"]
    for line in ("C                        136         6.67                 7.95              7.44",
                 "F                        130        10.00                 4.50              6.70",
                 "B                        140         4.44                 7.05              6.01",
                 "E                        148         0.00                 7.50              4.50",
                 "Purchases 2530.00 + fixed costs 50.00 = 2580.00 kEUR/year"):
        assert line in out


def test_local_search_script(outputs):
    out = outputs["supplier_selection_local_search.py"]
    assert "2^5 - 1 = 31" in out and "cover the six components: 21" in out
    assert "Step 1: remove A       -> B, C, D        2585.00" in out
    assert "Step 1: add C          -> C, E           2545.00" in out
    assert "Local optima among the 21 selections: C, E (2545.00); B, C, D (2585.00)" in out


def test_local_search_script_agrees_with_the_package():
    from suppliers import local_search as ls
    from suppliers import selection as sel
    script = load("supplier_selection_local_search.py")
    assert script.covering_selections() == sel.covering_selections()
    assert [script.cost(s) for s in script.covering_selections()] == [
        sel.cost(s) for s in sel.covering_selections()]
    for start in (("A", "B", "C", "D"), ("E",), ("A", "B", "C", "D", "E")):
        assert [(m, s, v) for m, s, v in script.local_search(start)] == [
            (r["move"], r["selection"], r["cost"]) for r in ls.search(start)]


def test_solver_script(outputs):
    out = outputs["supplier_selection_solver.py"]
    assert "5 y and 18 x, 23 in all" in out
    assert "Purchases 2445.00 + fixed costs 100.00 = 2545.00 kEUR/year" in out
    assert "Saving against the buyer's rule: 85.00 kEUR/year" in out
    assert "Bound: 1777.50 kEUR/year" in out
    assert "Rounding up:   A, B, C, 1835.00 kEUR/year" in out
    assert "x[s,m] <= y[s]: 3 nodes" in out and "n[s] y[s]: 9 nodes" in out


def test_solver_script_trees_agree_with_the_package():
    from suppliers import model as mo
    from suppliers.data import REDUCED_M, REDUCED_S
    script = load("supplier_selection_solver.py")
    for formulation in ("pair", "supplier"):
        rows = script.branch_and_bound(formulation)
        nodes = mo.branch_and_bound(REDUCED_S, REDUCED_M, formulation)
        assert [(r[1], r[2]) for r in rows] == [(n["fixed"], n["bound"]) for n in nodes]
