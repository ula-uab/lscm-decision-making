"""Check that the script of the lot sizing at the plants reproduces the numbers of
lot_sizing.md, and that it agrees with the package."""

import importlib.util
import subprocess
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parents[1] / "cases" / "production_plan"
SCRIPT = "lot_sizing_solver.py"


def load():
    spec = importlib.util.spec_from_file_location(Path(SCRIPT).stem, CASE / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_prints_the_tables():
    out = subprocess.run([sys.executable, SCRIPT], cwd=CASE, capture_output=True, text=True,
                         check=True).stdout
    for text in ("orders of Granada for Mountain bikes in week 15: 8 bikes",
                 "City 1.218; Trekking 828; Mountain 488; Cargo 285; product mix 43,2 %; 29,4 %; 17,3 %; 10,1 %",
                 "All             290    345    403    616    669    496       2.819",
                 "cost 954.462,98 EUR; backorders 0 and lost sales 0 bikes",
                 "Jan 190; Feb 295; Mar 342; Apr 176; May 0; Jun 30",
                 "setup and holding cost 10.111,28 EUR; another plan with the same costs in: no month",
                 "setup and holding cost 11.758,88 EUR; another plan with the same costs in: no month",
                 "setup and holding cost 2.869,97 EUR; another plan with the same costs in: no month",
                 "Plant 1: capacity overload 173,77 h; setup and holding cost 13.446,46 EUR",
                 "Plant 2: capacity overload 216,69 h; setup and holding cost 16.557,69 EUR",
                 "Plant 2  Six months       1.000    822,24  238,75     66,88     5,89         6,7",
                 "Plant 1, Six-month product mix in every week: Feb",
                 "Plant 3, Half the setup times: May"):
        assert text in out


def test_script_agrees_with_the_package():
    from plants import lot_sizing as ls
    script = load()
    data = ls.base()
    assert script.orders == data["orders"]
    cost, values = script.solve_m4(script.orders)
    master = script.from_master_plan(values)
    assert master["x"] == data["shipments"]
    assert master["least"] == data["least stock"]
    for f in script.F:
        weeks, plan_cost, _ = script.weekly_plan(f, master["x"], master["least"])
        plan = ls.weekly_plan(f)
        assert plan_cost == plan["cost"]
        assert all(weeks[w]["assembled"] == plan["weeks"][w]["assembled"] for w in script.WEEKS)
