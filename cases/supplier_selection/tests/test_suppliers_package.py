"""Check that the package of the notebook reproduces the numbers of
supplier_selection.md, and that the notebook runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from suppliers import local_search as ls  # noqa: E402
from suppliers import matrix as mx  # noqa: E402
from suppliers import model as mo  # noqa: E402
from suppliers import selection as sel  # noqa: E402
from suppliers.data import REDUCED_M, REDUCED_S, c, q  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "supplier_selection.ipynb"

# Table 6: the 21 selections that cover every component, from the cheapest (kEUR/year)
TABLE_6 = [
    ("C", "E", 2545), ("E", 2580), ("B", "E", 2585), ("B", "C", "D", 2585), ("A", "C", "D", 2590),
    ("A", "C", "E", 2590), ("B", "C", "E", 2590), ("C", "D", "E", 2590), ("A", "B", "C", 2595),
    ("A", "B", "D", 2615), ("A", "E", 2620), ("D", "E", 2620), ("A", "B", "E", 2625),
    ("B", "D", "E", 2625), ("A", "B", "C", "D", 2630), ("A", "B", "C", "E", 2635),
    ("A", "C", "D", "E", 2635), ("B", "C", "D", "E", 2635), ("A", "D", "E", 2660),
    ("A", "B", "D", "E", 2665), ("A", "B", "C", "D", "E", 2680),
]


def test_table3_scorecard_and_acceptable_suppliers():
    assert {s: round(v, 2) for s, v in q.items()} == {
        "A": 7.15, "B": 7.05, "C": 7.95, "D": 6.85, "E": 7.50, "F": 4.50}
    assert sel.ACCEPTABLE == ["A", "B", "C", "D", "E"]
    assert c["C"]["batteries"] == 680 and c["F"]["batteries"] == 650


def test_table4_decision_matrix_of_the_batteries():
    assert {s: round(v, 2) for s, v in mx.price_scores("batteries").items()} == {
        "B": 4.44, "C": 6.67, "E": 0.0, "F": 10.0}
    with_price = mx.with_price("batteries", 0.40)
    assert {s: round(v, 2) for s, v in with_price.items()} == {"C": 7.44, "F": 6.70, "B": 6.01, "E": 4.50}
    assert mx.ranking(with_price) == ["C", "F", "B", "E"]
    assert {k: round(100 * v) for k, v in mx.weights_with_price(0.40).items()} == {
        "Quality": 21, "Delivery reliability": 15, "Sustainability": 12, "Financial strength": 12, "Price": 40}
    assert mx.ranking(mx.with_price("batteries", 0)) == ["C", "E", "B", "F"]


def test_table5_buyer_rule_and_distributor_alone():
    rule = sel.buyer_rule()
    assert rule == {"frames": "C", "motors": "B", "batteries": "C", "wheels": "C", "brakes": "A",
                    "displays": "D"}
    assert sel.contracted_by(rule) == ("A", "B", "C", "D")
    assert sel.purchase_cost(rule) == 2430
    assert sel.cost(("A", "B", "C", "D")) == 2630
    assert sel.cost(("E",)) == 2580


def test_table6_number_of_selections():
    assert len(sel.all_selections()) == 31
    covering = sel.covering_selections()
    assert [(*s, sel.cost(s)) for s in covering] == TABLE_6
    assert sel.uncovered(("A", "B")) == ["wheels"]


def test_table7_optimum_of_the_model():
    solution = mo.solve()
    assert solution["variables"] == 23
    assert solution["cost"] == pytest.approx(2545)
    assert mo.contracted(solution) == ("C", "E")
    assert mo.purchase(solution) == {"frames": "C", "motors": "E", "batteries": "C", "wheels": "C",
                                     "brakes": "E", "displays": "E"}
    rule = sel.buyer_rule()
    optimum = mo.purchase(solution)
    assert sel.purchase_cost(optimum) - sel.purchase_cost(rule) == 15
    assert sel.cost(("A", "B", "C", "D")) - solution["cost"] == pytest.approx(85)
    relaxation = mo.solve(relax=True)
    assert relaxation["cost"] == pytest.approx(2545) and mo.is_integer(relaxation)


def test_table8_local_search():
    from_rule = ls.search(("A", "B", "C", "D"))
    assert [(r["move"], r["selection"], r["cost"]) for r in from_rule] == [
        ("start", ("A", "B", "C", "D"), 2630), ("remove A", ("B", "C", "D"), 2585)]
    assert sel.assign(("B", "C", "D"))["brakes"] == "D"
    best = sorted((sel.cost(new), move) for move, new in ls.neighbours(("B", "C", "D")))[:3]
    assert best == [(2590, "swap B for A"), (2590, "swap B for E"), (2590, "swap D for E")]
    assert [move for move, _ in ls.blocked(("B", "C", "D"))] == ["remove B", "remove C", "remove D"]
    # The optimum is two moves away, and the first one raises the cost
    assert sel.cost(("B", "C", "E")) == 2590 and sel.cost(("C", "E")) == 2545
    from_e = ls.search(("E",))
    assert [(r["move"], r["selection"], r["cost"]) for r in from_e] == [
        ("start", ("E",), 2580), ("add C", ("C", "E"), 2545)]
    assert ls.local_optima(sel.covering_selections()) == [("C", "E"), ("B", "C", "D")]


def test_reduced_version_costs_and_relaxation():
    costs = {s: sel.cost(s, REDUCED_M) for s in sel.all_selections(REDUCED_S)}
    assert costs == {("A",): None, ("B",): None, ("C",): None, ("A", "B"): 1810, ("A", "C"): 1795,
                     ("B", "C"): 1785, ("A", "B", "C"): 1835}
    r = mo.solve(REDUCED_S, REDUCED_M, "pair", relax=True)
    assert r["cost"] == pytest.approx(1777.5)
    assert all(v == pytest.approx(0.5) for v in list(r["y"].values()) + list(r["x"].values()))
    assert mo.rounded(r, up=True) == ("A", "B", "C")
    assert mo.rounded(r, up=False) == ()
    best = mo.solve(REDUCED_S, REDUCED_M, "pair")
    assert mo.contracted(best) == ("B", "C") and best["cost"] == pytest.approx(1785)


def _tree(nodes):
    return [(n["fixed"], None if n["bound"] is None else round(n["bound"], 1),
             None if n["y"] is None else tuple(round(abs(v), 2) for v in n["y"].values()), n["outcome"])
            for n in nodes]


def test_table10_tree_one_constraint_per_pair():
    nodes = mo.branch_and_bound(REDUCED_S, REDUCED_M, "pair")
    assert _tree(nodes) == [
        ({}, 1777.5, (0.5, 0.5, 0.5), "branch on y_A"),
        ({"A": 1}, 1795.0, (1, 0, 1), "integer: best known"),
        ({"A": 0}, 1785.0, (0, 1, 1), "integer: best known"),
    ]
    assert mo.best_of(nodes)["selection"] == ("B", "C")


def test_table11_tree_one_constraint_per_supplier():
    nodes = mo.branch_and_bound(REDUCED_S, REDUCED_M, "supplier")
    assert _tree(nodes) == [
        ({}, 1760.0, (0, 0.5, 1), "branch on y_B"),
        ({"B": 1}, 1780.0, (0, 1, 0.5), "branch on y_C"),
        ({"B": 1, "C": 1}, 1785.0, (0, 1, 1), "integer: best known"),
        ({"B": 1, "C": 0}, 1785.0, (0.5, 1, 0), "closed by the bound"),
        ({"B": 0}, 1770.0, (0.5, 0, 1), "branch on y_A"),
        ({"B": 0, "A": 1}, 1775.0, (1, 0, 0.5), "branch on y_C"),
        ({"B": 0, "A": 1, "C": 1}, 1795.0, (1, 0, 1), "closed by the bound"),
        ({"B": 0, "A": 1, "C": 0}, None, None, "no solution"),
        ({"B": 0, "A": 0}, None, None, "no solution"),
    ]
    assert [n.get("uncovered") for n in nodes[7:]] == [["batteries"], ["motors"]]
    assert mo.best_of(nodes)["selection"] == ("B", "C")


def test_wrong_selection_gives_a_clear_message():
    with pytest.raises(ValueError, match="Unknown supplier"):
        sel.selection(["A", "Z"])
    with pytest.raises(ValueError, match="without a supplier"):
        ls.search(("A", "B"))


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()


def _single_solution(formulation, fixed, bound):
    """True if the relaxation has one optimal solution: every variable has the same
    minimum and maximum among the solutions that cost no more than the bound."""
    import pulp
    from suppliers.data import a, f
    pairs = [(s, m) for s in REDUCED_S for m in REDUCED_M if a[s][m]]
    for target in [("y", s) for s in REDUCED_S] + [("x", p) for p in pairs]:
        values = []
        for sense in (pulp.LpMinimize, pulp.LpMaximize):
            model = pulp.LpProblem("unique", sense)
            y = {s: model.add_variable(f"y_{s}", lowBound=fixed.get(s, 0), upBound=fixed.get(s, 1))
                 for s in REDUCED_S}
            x = {p: model.add_variable(f"x_{p[0]}_{p[1]}", lowBound=0, upBound=1) for p in pairs}
            model += y[target[1]] if target[0] == "y" else x[target[1]]
            for m in REDUCED_M:
                model += pulp.lpSum(x[s, n] for s, n in pairs if n == m) == 1
            if formulation == "pair":
                for s, m in pairs:
                    model += x[s, m] <= y[s]
            else:
                for s in REDUCED_S:
                    offers = [m for n, m in pairs if n == s]
                    model += pulp.lpSum(x[s, m] for m in offers) <= len(offers) * y[s]
            model += (pulp.lpSum(f[s] * y[s] for s in REDUCED_S)
                      + pulp.lpSum(c[s][m] * x[s, m] for s, m in pairs) <= bound + 1e-7)
            model.solve(pulp.HiGHS(msg=False))
            values.append(pulp.value(model.objective))
        if abs(values[0] - values[1]) > 1e-6:
            return False
    return True


@pytest.mark.parametrize("formulation", mo.FORMULATIONS)
def test_the_relaxation_of_every_node_has_one_solution(formulation):
    for node in mo.branch_and_bound(REDUCED_S, REDUCED_M, formulation):
        if node["bound"] is not None:
            assert _single_solution(formulation, node["fixed"], node["bound"])
