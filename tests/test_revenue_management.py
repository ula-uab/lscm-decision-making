"""Check that the script of the revenue management case reproduces the numbers of
revenue_management.md, and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1] / "cases" / "revenue_management"
SCRIPT = "revenue_management_solver.py"


def load():
    spec = importlib.util.spec_from_file_location(Path(SCRIPT).stem, CASE / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("Revenue of the rule: 39,465.00 EUR",
                 "The rule loses 1,770.00 EUR, 4.3 % of the optimal revenue",
                 "BCN-HEL   Economy BASIC        80.00      2.00         78.00    8,580.00",
                 "Demand of BCN-RIX Economy BASIC           no     55.00  tickets",
                 "RIX->HEL                     35.00                35.00               -35.00",
                 "RIX-HEL   Economy BASIC      45.00       35.00                       10.00",
                 "RIX->HEL    BCN-HEL Economy BASIC                1.00          2.00           3.00                           110.00",
                 "RIX->HEL    BCN-RIX Economy BASIC              106.00        105.00         104.00                           -75.00",
                 "BCN->RIX         75.00 EUR/seat    115.00    275.00",
                 "RIX->HEL         35.00 EUR/seat    138.00    218.00",
                 "    10            120.00          100.00                20.00",
                 "    10            100.00         -100.00              -180.00",
                 "   180      42,635.00      1,400.00        1,400.00           yes           1,200.00      200.00",
                 "   120      40,355.00       -880.00         -700.00            no            -800.00      -80.00"):
        assert text in out


def test_script_agrees_with_the_package():
    from fares import model as m
    from fares.data import C, D, L, P, r
    script = load()
    # The script names flights and trips in plain ASCII; the order is the same as in the package
    assert [script.r[p] for p in script.P] == [r[p] for p in P]
    assert [script.D[p] for p in script.P] == [D[p] for p in P]
    assert [script.C[l] for l in script.L] == [C[l] for l in L]
    revenue, plan, bid, demand_price = script.solve_model(script.C, script.D)
    package = m.solve()
    assert revenue == package["revenue"]
    assert [plan[p] for p in script.P] == [package["plan"][p] for p in P]
    assert [bid[l] for l in script.L] == [package["bid price"][l] for l in L]
    assert [demand_price[p] for p in script.P] == [package["demand price"][p] for p in P]
    rule = script.highest_fare_first(script.C, script.D)
    assert [rule[p] for p in script.P] == [m.highest_fare_first()["plan"][p] for p in P]
    for ls, lp in zip(script.L, L):
        assert script.validity_range(ls, script.C, script.D) == m.validity_range(lp)
