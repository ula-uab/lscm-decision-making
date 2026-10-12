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
    for text in ("Total                      208.00      220.00      36,480.00",
                 "Demand of Economy BASIC          64.00           140.00       no     76.00  tickets",
                 "Capacity of the cabin                           75.00                    36,555.00         75.00",
                 "Demand of Business                             307.50                    36,787.50        307.50",
                 "Demand of Economy FLEX                         105.00                    36,585.00        105.00",
                 "Capacity of the cabin                75.00      156.00      296.00  seats",
                 "Demand of Business                  307.50        0.00       66.67  tickets",
                 "Demand of Economy FLEX              105.00       44.00      184.00  tickets",
                 "Demand of Economy BASIC               0.00       64.00    no limit  tickets",
                 "          156         296             75.00",
                 "   180     24.00  120.00   24.00      33,480.00    3,000.00                  3,000.00",
                 "   150     24.00  114.00    0.00      30,600.00    5,880.00                  5,250.00"):
        assert text in out


def test_script_agrees_with_the_package():
    from fares import model as m
    from fares.data import C, D, F
    script = load()
    assert script.F == F and script.C == C and script.D == D
    for capacity in (C, 180, 150):
        revenue, plan, prices = script.solve_model(capacity, D)
        package = m.solve(capacity)
        assert revenue == package["revenue"] and plan == package["plan"]
        assert prices == {"capacity": package["bid price"], **package["demand price"]}
    for key in script.KEYS:
        assert script.validity_range(key, C, D) == m.validity_range(key)
    assert [(p["from"], p["to"], p["slope"]) for p in m.segments()] == list(script.segments(D))
