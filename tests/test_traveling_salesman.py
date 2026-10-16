"""Check that the two scripts of the traveling salesman case print the same
numbers as the package."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

CASE = Path(__file__).resolve().parents[1] / "cases" / "traveling_salesman"
SCRIPTS = ["traveling_salesman_heuristics.py", "traveling_salesman_local_optima.py"]


def load(script):
    spec = importlib.util.spec_from_file_location(Path(script).stem, CASE / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(script):
    return subprocess.run([sys.executable, script], cwd=CASE, capture_output=True, text=True,
                          encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                          check=True).stdout


@pytest.fixture(scope="module")
def outputs():
    return {script: run(script) for script in SCRIPTS}


def test_heuristics_script_prints_the_routes_of_the_package(outputs):
    from routes import construction as co
    from routes import local_search as ls
    from routes.data import ABBR
    out = outputs["traveling_salesman_heuristics.py"]
    nn, sw = co.nearest_neighbor(), co.sweep()
    assert f"Nearest neighbor: {co.label(nn)}, {co.length(nn):,} km" in out
    assert f"Sweep: {co.label(sw)}, {co.length(sw):,} km" in out
    for i in sw[1:-1]:
        assert f"{ABBR[i]:<6}{co.angle(i):>16.1f}" in out
    after, rows = ls.ivanov_pass(nn)
    for r in rows:
        assert (f"{r['iteration']:<5}{co.label(r['sub_path']):<22}{r['before']:>8}{r['after']:>8}  "
                f"{'yes' if r['confirmed'] else ''}") in out
    assert f"After the pass: {co.label(after)}, {co.length(after):,} km" in out
    for start, move in ((nn, "swap"), (nn, "reversal"), (sw, "reversal")):
        steps = ls.search(start, move)
        for s in steps[1:]:
            arcs_out = "; ".join(map(ls.arc_label, s["out"]))
            arcs_in = "; ".join(map(ls.arc_label, s["in"]))
            assert (f"{s['step']:<6}{co.label(s['reversed']):<34}{arcs_out:<18}{arcs_in:<18}"
                    f"{s['length']:>7,}") in out
        assert f"Stops at {co.label(steps[-1]['route'])}, {steps[-1]['length']:,} km" in out


def test_heuristics_script_agrees_with_the_package():
    from routes import construction as co
    from routes import local_search as ls
    script = load("traveling_salesman_heuristics.py")
    assert script.d == co.d
    for start in (co.nearest_neighbor(), co.sweep(), co.random_route(7)):
        for move in ls.MOVES:
            assert [s[3] for s in script.local_search(start, move)] == [
                s["route"] for s in ls.search(start, move)]


def test_local_optima_script_prints_the_numbers_of_the_package(outputs):
    from routes import construction as co
    from routes import exact as ex
    from routes import local_search as ls
    out = outputs["traveling_salesman_local_optima.py"]
    script = load("traveling_salesman_local_optima.py")
    shortest, routes = ex.shortest_routes()
    assert f"Shortest route: {shortest:,} km" in out
    assert f"Routes with that length: {len(routes)}" in out
    for r in routes:
        assert f"  {co.label(r)}" in out
    nn = co.nearest_neighbor()
    for r in (nn, co.sweep(), ls.ivanov_pass(nn)[0], ls.local_optimum(nn, "swap")):
        assert f"{co.length(r):>7,}{ex.gap(r, shortest):>19.1f} %" in out
    stops = ls.random_starts(script.STARTS, script.SEED, "reversal")
    for km, count in stops.items():
        assert f"{km:<28,}{count:>16,}{100 * count / script.STARTS:>8.1f}" in out
    assert f"Different lengths where the search stops: {len(stops)}" in out


def test_local_optima_script_agrees_with_the_package():
    from routes import construction as co
    from routes import exact as ex
    from routes import local_search as ls
    script = load("traveling_salesman_local_optima.py")
    assert script.shortest_routes() == ex.shortest_routes()
    nn = co.nearest_neighbor()
    assert script.ivanov_pass(nn) == ls.ivanov_pass(nn)[0]
    assert script.random_starts(500, 3) == ls.random_starts(500, 3, "reversal")
