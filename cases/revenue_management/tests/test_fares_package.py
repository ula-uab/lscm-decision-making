"""Check that the package of the notebook reproduces the numbers of
revenue_management.md, and that the notebook runs from start to end."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")

from fares import model as m  # noqa: E402
from fares.data import D, C  # noqa: E402

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks" / "revenue_management.ipynb"
BUSINESS, FLEX, BASIC = "Business", "Economy FLEX", "Economy BASIC"


def test_table2_optimal_plan():
    solution = m.solve()
    assert solution["plan"] == {BUSINESS: 24, FLEX: 120, BASIC: 64}
    assert solution["revenue"] == pytest.approx(36480)
    assert solution["seats"] == pytest.approx(220)


def test_table3_binding_constraints_and_slack():
    solution = m.solve()
    assert solution["spare seats"] == 0
    assert solution["unsold demand"] == {BUSINESS: 0, FLEX: 0, BASIC: 76}


def test_table4_shadow_prices_are_the_rise_in_revenue():
    solution = m.solve()
    assert solution["bid price"] == pytest.approx(75)
    assert solution["demand price"] == {BUSINESS: pytest.approx(307.5), FLEX: pytest.approx(105), BASIC: 0}
    # Solving again with one more seat or one more ticket of demand gives the same change
    for key, change in (("capacity", 75), (BUSINESS, 307.5), (FLEX, 105), (BASIC, 0)):
        check = m.one_more(key)
        assert check["change"] == pytest.approx(change)
        assert check["change"] == pytest.approx(check["shadow price"])


def test_table5_ranges():
    assert m.validity_range("capacity") == (156, 296)
    low, high = m.validity_range(BUSINESS)
    assert low == 0 and high == pytest.approx(200 / 3, abs=1e-5)
    assert m.validity_range(FLEX) == (44, 184)
    assert m.validity_range(BASIC) == (64, None)


def test_table6_revenue_against_capacity():
    pieces = m.segments()
    assert [(p["from"], p["to"], p["slope"]) for p in pieces] == [
        (0, 36, 280), (36, 156, 180), (156, 296, 75), (296, 320, 0)]
    assert [p["fare"] for p in pieces] == [BUSINESS, FLEX, BASIC, None]


def test_table7_another_capacity():
    inside = m.other_capacity(180)
    assert inside["new"]["plan"] == {BUSINESS: 24, FLEX: 120, BASIC: 24}
    assert inside["new"]["revenue"] == pytest.approx(33480)
    assert inside["change"] == pytest.approx(-3000) and inside["estimate"] == pytest.approx(-3000)
    assert inside["inside"]
    outside = m.other_capacity(150)
    assert outside["new"]["plan"] == {BUSINESS: 24, FLEX: 114, BASIC: 0}
    assert outside["new"]["revenue"] == pytest.approx(30600)
    assert outside["change"] == pytest.approx(-5880) and outside["estimate"] == pytest.approx(-5250)
    assert not outside["inside"]


def test_one_source_of_data():
    # The model, the tables and the figures read the same demand and capacity
    assert m.D is D and m.C == C


def test_notebook_runs():
    nbformat = pytest.importorskip("nbformat")
    nbclient = pytest.importorskip("nbclient")
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nbclient.NotebookClient(nb, timeout=180, kernel_name="python3",
                            resources={"metadata": {"path": str(NOTEBOOK.parent)}}).execute()
