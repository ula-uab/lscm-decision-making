"""Check that the package of the notebook reproduces the numbers of
traveling_salesman.md, and that the notebook runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from routes import construction as co  # noqa: E402
from routes import exact as ex  # noqa: E402
from routes import local_search as ls  # noqa: E402
from routes.data import ABBR, CITIES, d, euclidean  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "traveling_salesman.ipynb"
CODE = {abbr: i for i, abbr in ABBR.items()}


def route(text):
    """[1, 6, 5, ...] for 'HH, HL, KI, ...'."""
    return [CODE[a] for a in text.split(", ")]


NEAREST = route("HH, HL, KI, HR, BHV, OL, HB, H, HIL, SZG, BS, WOB, GÖ, OS, HH")
SWEEP = route("HH, BHV, OL, HB, OS, H, HIL, GÖ, SZG, BS, WOB, HR, HL, KI, HH")
AFTER_PASS = route("HH, HL, HR, KI, BHV, OL, HB, H, HIL, SZG, BS, WOB, GÖ, OS, HH")
SHORTEST_1 = route("HH, BHV, OL, HB, OS, H, HIL, GÖ, SZG, BS, WOB, HR, KI, HL, HH")
SHORTEST_2 = route("HH, HL, HR, KI, BHV, OL, HB, OS, H, HIL, GÖ, SZG, BS, WOB, HH")

# Table 5: iteration, sub-path, length before and after the swap (km)
TABLE_5 = [
    (1, "HH, HL, KI, HR", 354, 367), (2, "HL, KI, HR, BHV", 585, 493), (3, "HR, KI, BHV, OL", 447, 780),
    (4, "KI, BHV, OL, HB", 328, 433), (5, "BHV, OL, HB, H", 280, 333), (6, "OL, HB, H, HIL", 246, 536),
    (7, "HB, H, HIL, SZG", 222, 295), (8, "H, HIL, SZG, BS", 112, 153), (9, "HIL, SZG, BS, WOB", 97, 169),
    (10, "SZG, BS, WOB, GÖ", 240, 242), (11, "BS, WOB, GÖ, OS", 405, 554), (12, "WOB, GÖ, OS, HH", 662, 798),
]

# Table 7: sub-path reversed, arcs out, arcs in, length (km)
TABLE_7 = [
    ("", "", "", 1745),
    ("KI, HR", "HL–KI; HR–BHV", "HL–HR; KI–BHV", 1653),
    ("H, HIL, SZG, BS, WOB, GÖ, OS", "HB–H; OS–HH", "HB–OS; H–HH", 1592),
    ("WOB, BS, SZG, HIL, H", "GÖ–WOB; H–HH", "GÖ–H; WOB–HH", 1558),
    ("H, HIL", "GÖ–H; HIL–SZG", "GÖ–HIL; H–SZG", 1550),
    ("GÖ, HIL, H", "OS–GÖ; H–SZG", "OS–H; GÖ–SZG", 1536),
]

# Table 9: length where the search stops (km) and number of starting routes,
# from 20,000 random routes drawn after random.seed(1)
TABLE_9 = {1536: 15144, 1554: 1785, 1572: 758, 1587: 320, 1588: 1241, 1603: 323, 1610: 370, 1622: 40,
           1637: 19}


def test_table2_distances_are_symmetric_and_match_the_coordinates():
    assert all(d[i][j] == d[j][i] for i in CITIES for j in CITIES)
    assert all(d[i][i] == 0 for i in CITIES)
    assert all(d[i][j] == round(euclidean(i, j)) for i in CITIES for j in CITIES)
    assert max(abs(d[i][j] - euclidean(i, j)) for i in CITIES for j in CITIES) == pytest.approx(0.49, abs=0.005)


def test_table3_nearest_neighbor():
    assert co.nearest_neighbor() == NEAREST
    assert co.length(NEAREST) == 1745
    assert [km for _, _, km in co.legs(NEAREST)][-2:] == [205, 284]


def test_table4_sweep():
    assert co.sweep() == SWEEP
    assert co.length(SWEEP) == 1549
    assert [round(co.angle(i), 1) for i in SWEEP[1:-1]] == [93.3, 116.0, 131.4, 144.7, 174.2, 179.1, 179.4,
                                                            185.8, 192.4, 198.3, 297.3, 312.4, 356.4]


def test_table5_pass_of_ivanov():
    after, rows = ls.ivanov_pass(NEAREST)
    assert [(r["iteration"], co.label(r["sub_path"]), r["before"], r["after"]) for r in rows] == TABLE_5
    assert [r["iteration"] for r in rows if r["confirmed"]] == [2]
    assert after == AFTER_PASS
    assert co.length(after) == 1653


def test_neighborhoods():
    assert len(ls.moves("swap")) == 12 and len(ls.moves("reversal")) == 78
    assert set(ls.moves("swap")) <= set(ls.moves("reversal"))
    for i, j in ls.moves("reversal"):
        assert co.length(ls.apply(NEAREST, i, j)) - co.length(NEAREST) == ls.change(NEAREST, i, j)


def test_swap_search_from_the_nearest_neighbor():
    steps = ls.search(NEAREST, "swap")
    assert [s["length"] for s in steps] == [1745, 1653]
    assert co.label(steps[1]["reversed"]) == "KI, HR"
    assert steps[-1]["route"] == AFTER_PASS
    assert co.length(AFTER_PASS) + ls.best_move(AFTER_PASS, "swap")[2] == 1655


def test_table7_reversal_search_from_the_nearest_neighbor():
    steps = ls.search(NEAREST, "reversal")
    assert [(co.label(s["reversed"]), "; ".join(map(ls.arc_label, s["out"])),
             "; ".join(map(ls.arc_label, s["in"])), s["length"]) for s in steps] == TABLE_7
    assert steps[-1]["route"] == SHORTEST_2
    assert ls.local_optimum(NEAREST, "reversal") == SHORTEST_2


def test_reversal_search_from_the_sweep():
    steps = ls.search(SWEEP, "reversal")
    assert [s["length"] for s in steps] == [1549, 1536]
    assert co.label(steps[1]["reversed"]) == "HL, KI"
    assert steps[-1]["route"] == SHORTEST_1


def test_shortest_route():
    shortest, routes = ex.shortest_routes()
    assert shortest == 1536
    assert len(routes) == 4
    assert ex.distinct(routes) == [SHORTEST_1, SHORTEST_2]
    assert all(co.length(r) == 1536 for r in routes)


def test_table8_heuristics_against_the_shortest_route():
    gaps = {name: round(ex.gap(r, 1536), 1) for name, r in [
        ("nearest", NEAREST), ("sweep", SWEEP), ("pass", AFTER_PASS)]}
    assert gaps == {"nearest": 13.6, "sweep": 0.8, "pass": 7.6}


def test_table9_local_optima_from_random_routes():
    assert ls.random_starts(20000, seed=1, move="reversal") == TABLE_9


def test_random_routes_are_the_draws_of_random_seed():
    import random
    random.seed(1)
    expected = []
    for _ in range(3):
        order = list(range(2, 15))
        random.shuffle(order)
        expected.append([1] + order + [1])
    rng = random.Random(1)
    assert [co.random_route(rng=rng) for _ in range(3)] == expected
    assert co.random_route(seed=1) == expected[0]


def test_document_figures(tmp_path):
    paths = __import__("routes").document_figures(tmp_path)
    assert [p.name for p in paths] == ["nearest_neighbor.png", "sweep.png", "local_search.png"]
    assert all(p.stat().st_size > 0 for p in paths)


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
