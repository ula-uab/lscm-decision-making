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
    for text in ("Revenue: 41,235.00 EUR",
                 "BCN-HEL                 6.00           20.00            2.00",
                 "Demand of BCN-RIX Economy BASIC           no     55.00  tickets",
                 "Demand of BCN-HEL Economy BASIC           no     78.00  tickets",
                 "RIX->HEL                     35.00                35.00               -35.00",
                 "RIX-HEL   Economy BASIC      45.00       35.00                       10.00",
                 "RIX->HEL    BCN-HEL Economy BASIC                1.00          2.00           3.00                           110.00",
                 "RIX->HEL    BCN-RIX Economy BASIC              106.00        105.00         104.00                           -75.00",
                 "BCN->RIX         75.00 EUR/seat    115.00    275.00",
                 "RIX->HEL         35.00 EUR/seat    138.00    218.00",
                 "    10            120.00          100.00                20.00",
                 "    10            100.00         -100.00              -180.00",
                 "RIX-HEL   Economy FLEX        40.00                      65.00        0.00       42.00",
                 "BCN-HEL   Economy BASIC       80.00                       0.00        2.00    no limit",
                 "Revenue: 41,805.00 EUR, 570.00 EUR. Estimate with the shadow price: 650.00 EUR",
                 "Net result: -30.00 EUR; with the estimate, 50.00 EUR",
                 "The demand of 50.00 tickets is outside the range (0.00 to 42.00 tickets)",
                 "Change in revenue with 1, 2, 3, 5 and 10 tickets more of demand (EUR): "
                 "65.00, 130.00, 185.00, 295.00, 570.00",
                 "Bid prices with the new demand: BCN->RIX 75.00 EUR/seat, RIX->HEL 45.00 EUR/seat"):
        assert text in out


def test_script_agrees_with_the_package():
    from fares import model as m
    from fares.data import CHANGE_COST, CHANGE_DEMAND, CHANGE_PRODUCT, C, D, L, P, r
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
    for ls, lp in zip(script.L, L):
        assert script.validity_range("seats", ls, script.C, script.D) == m.validity_range("seats", lp)
    for ps, pp in zip(script.P, P):
        assert script.validity_range("demand", ps, script.C, script.D) == m.validity_range("demand", pp)
    # The campaign of §5: the same fare of the same trip, demand and cost
    assert (script.CHANGE_PRODUCT[1], script.CHANGE_DEMAND, script.CHANGE_COST) == (
        CHANGE_PRODUCT[1], CHANGE_DEMAND, CHANGE_COST)
