"""Checks of the operators against the examples of their sources, of the local
search against the case, and of the exact shortest route of the 14 cities.

Run: uv run --with deap==1.4.4 pytest cases/traveling_salesman/experiments
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import exact  # noqa: E402
import instances  # noqa: E402
import methods  # noqa: E402
import operators as op  # noqa: E402
from routes import construction, local_search as case_ls  # noqa: E402


class Scripted:
    """Makes the choices of an example: ``choice`` returns the next scripted
    city, which must be one of the options."""
    def __init__(self, picks):
        self.picks = list(picks)

    def choice(self, options):
        pick = self.picks.pop(0)
        assert pick in options, (pick, options)
        return pick


def test_ox1_example_of_larranaga(monkeypatch):
    # §4.3.3: parents (1 2 3 4 5 6 7 8) and (2 4 6 8 7 5 3 1), cut points
    # after the second and after the fifth position
    monkeypatch.setattr(random, "sample", lambda population, k: [2, 4])
    x = [c - 1 for c in (1, 2, 3, 4, 5, 6, 7, 8)]
    y = [c - 1 for c in (2, 4, 6, 8, 7, 5, 3, 1)]
    c1, c2 = op.ox1(x, y)
    assert [c + 1 for c in c2] == [8, 7, 3, 4, 5, 1, 2, 6]
    assert [c + 1 for c in c1] == [4, 5, 6, 8, 7, 1, 2, 3]


def test_edge_map_table_3_of_larranaga():
    edges = op.edge_map([1, 2, 3, 4, 5, 6], [2, 4, 3, 1, 5, 6])
    assert edges == {1: {2, 6, 3, 5}, 2: {1, 3, 4, 6}, 3: {2, 4, 1}, 4: {3, 5, 2},
                     5: {4, 6, 1}, 6: {1, 5, 2}}


def test_er_example_of_larranaga():
    # §4.3.7: start at 2 (tie with 1), then 3 (tie with 4 and 6), 4, 5, 1 (tie with 6), 6
    child = op.er([1, 2, 3, 4, 5, 6], [2, 4, 3, 1, 5, 6], Scripted([2, 3, 4, 5, 1, 6]))
    assert child == [2, 3, 4, 5, 1, 6]


def test_er_child_of_a_route_with_itself_is_that_route():
    # every city has two edges, so ER never has to break an edge (step 5 is not reached
    # before the end) and the child is the parent route, in one direction or the other
    random.seed(3)
    for _ in range(200):
        x = random.sample(range(30), 30)
        child = op.er(x, x)
        edges = {frozenset(e) for e in zip(x, x[1:] + x[:1])}
        assert {frozenset(e) for e in zip(child, child[1:] + child[:1])} == edges


def test_ivm_example_of_larranaga():
    # §4.3.16: sub-tour (3 4 5) inserted reversed after city 7
    assert op.ivm([1, 2, 3, 4, 5, 6, 7, 8], start=2, end=4, at=4) == [1, 2, 6, 7, 5, 4, 3, 8]


def test_one_point_and_exchange_example_of_klein_and_faust():
    # Fig. 31.3 and the text of §31.4
    a, b = op.one_point([1, 2, 3, 4, 5, 6, 7, 8], [2, 3, 1, 5, 6, 4, 8, 7], h=4)
    assert a == [1, 2, 3, 4, 5, 6, 8, 7]
    assert b == [2, 3, 1, 5, 4, 6, 7, 8]
    assert op.exchange(a, 2, 5) == [1, 2, 6, 4, 5, 3, 8, 7]


def test_tournament_keeps_the_shorter_of_each_pair():
    random.seed(1)
    lengths = [random.randint(100, 200) for _ in range(50)]
    random.seed(7)
    pool = op.tournament(lengths, 50)
    random.seed(7)
    order = list(range(50))
    random.shuffle(order)
    first = [min(order[k:k + 2], key=lambda i: lengths[i]) for k in range(0, 50, 2)]
    assert pool[:25] == first and len(pool) == 50


def test_local_search_is_the_one_of_the_case():
    # From the nearest neighbor: five steps to 1,536 km (Table 7 of the case), with
    # (n - 1)(n - 2)/2 = 78 moves evaluated in each of the six scans
    d = instances.ivanov14()
    start = [c - 1 for c in construction.nearest_neighbor()[:-1]]
    t = methods.Tracker(d, 10**6)
    route, length = methods.local_search(start, t.evaluate(start), t)
    case = case_ls.search(construction.nearest_neighbor(), "reversal")
    assert length == 1536 == case[-1]["length"]
    assert [c + 1 for c in route] + [1] == case[-1]["route"]
    assert t.evaluations == 1 + 6 * 78
    assert [c[1] for c in t.curve] == [s["length"] for s in case]


def test_methods_stop_at_the_budget():
    d = instances.case("random20")
    for method in methods.METHODS[1:]:
        result = methods.run(method, d, 5000, seed=1)
        assert result["evaluations"] == 5000
        assert result["curve"][-1][1] == result["best"]


def test_exact_shortest_route_of_the_case():
    assert exact.shortest(instances.ivanov14())["length"] == 1536
