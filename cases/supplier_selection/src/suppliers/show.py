"""What the notebook shows: tables, figures and short messages.

Each function answers one step of the notebook, so that its cells only need
one line of code.
"""

from __future__ import annotations

import functools

import matplotlib.pyplot as plt
import pandas as pd

from . import local_search as ls
from . import matrix as mx
from . import model as mo
from . import selection as sel
from .data import (CRITERIA, MIN_SCORE, PRICE, PRICE_WEIGHT, REDUCED_M, REDUCED_S, SCORES, VOLUME,
                   WEIGHTS, M, S, c, f, q)

FIXED = "tab:orange"
PURCHASE = "tab:blue"
BEST = "tab:green"


def _light(func):
    """Draw with matplotlib's default style: white background and dark text, also
    when the editor has a dark theme."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with plt.style.context("default"):
            return func(*args, **kwargs)
    return wrapper


def _display(obj) -> None:
    try:
        from IPython.display import display
        display(obj)
    except ImportError:
        print(obj)


def _k(x: float) -> str:
    return f"{x:,.0f} k€/year"


def _purchase_table(purchase: dict) -> pd.DataFrame:
    return pd.DataFrame({m: {"Supplier": s, "Annual cost (k€/year)": c[s][m]}
                         for m, s in purchase.items()}).T.rename_axis("Component")


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def price_table() -> pd.DataFrame:
    """Table 1: price of each component at each supplier (€/unit); '–' if not offered."""
    return pd.DataFrame({s: {m: PRICE[s].get(m, "–") for m in M} for s in S}).T.rename_axis("Supplier")


def cost_table() -> pd.DataFrame:
    """Annual cost c[s][m] of buying the whole volume of m from s (k€/year)."""
    return pd.DataFrame({s: {m: c[s].get(m, "–") for m in M} for s in S}).T.rename_axis("Supplier")


def scorecard_table() -> pd.DataFrame:
    """Table 2: scorecard of each supplier, weighted score and whether it is acceptable."""
    rows = {s: {**{f"{k} ({100 * WEIGHTS[k]:.0f} %)": SCORES[s][k] for k in CRITERIA},
                "Weighted score q": round(q[s], 2),
                "Acceptable (q ≥ 6)": "yes" if q[s] >= MIN_SCORE else "no"} for s in S}
    return pd.DataFrame(rows).T.rename_axis("Supplier")


def show_data() -> None:
    """Prices, annual costs, fixed cost and scorecard."""
    print(f"Prices (€/unit). The company assembles {VOLUME:,} bicycles a year.")
    _display(price_table())
    print(f"Annual cost of buying the whole volume of a component from a supplier (k€/year): "
          f"price × {VOLUME:,} / 1,000.")
    _display(cost_table())
    print(f"Fixed cost of each contracted supplier: {f['A']} k€/year.")
    print()
    print("Scorecard (points, 0-10) and weighted score:")
    _display(scorecard_table())


# ---------------------------------------------------------------------------
# §3 Decision matrix for the batteries
# ---------------------------------------------------------------------------

@_light
def batteries_matrix(price_weight_percent: float = 100 * PRICE_WEIGHT) -> None:
    """The decision matrix of the batteries without the price and with the price
    weighing price_weight_percent %."""
    w = price_weight_percent / 100
    suppliers = mx.offering("batteries")
    ps = mx.price_scores("batteries")
    weights = mx.weights_with_price(w)
    with_price = mx.with_price("batteries", w)
    table = pd.DataFrame({s: {
        **{f"{k} ({100 * weights[k]:.0f} %)": SCORES[s][k] for k in CRITERIA},
        f"Price score ({100 * w:.0f} %)": round(ps[s], 2),
        "Price (€/unit)": PRICE[s]["batteries"],
        "Score without price": round(q[s], 2),
        "Score with price": round(with_price[s], 2),
    } for s in suppliers}).T.rename_axis("Supplier")
    _display(table.sort_values("Score with price", ascending=False))
    order = mx.ranking(with_price)
    print("Ranking with the price: " + " > ".join(f"{s} ({with_price[s]:.2f})" for s in order))
    if order[0] == "F" or order.index("F") < order.index("E"):
        print(f"F, with a quality score of {SCORES['F']['Quality']}, is ranked above suppliers with a "
              "much better scorecard: a low price makes up for poor quality.")

    fig, ax = plt.subplots(figsize=(7, 3.2))
    xs = range(len(suppliers))
    ax.bar([x - 0.2 for x in xs], [q[s] for s in suppliers], width=0.4, color="0.6", label="without price")
    ax.bar([x + 0.2 for x in xs], [with_price[s] for s in suppliers], width=0.4, color=PURCHASE,
           label=f"with price ({100 * w:.0f} %)")
    ax.axhline(MIN_SCORE, color="black", ls=":", lw=1, label=f"acceptable: score ≥ {MIN_SCORE}")
    ax.set_xticks(list(xs), suppliers)
    ax.set_ylim(0, 10)
    ax.set_ylabel("Weighted score (points)")
    ax.set_title("Batteries: weighted score of each supplier", fontsize=10)
    ax.legend(fontsize=8, loc="upper right", ncol=3)
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()


# ---------------------------------------------------------------------------
# §4 The buyer's rule and the cost of any selection
# ---------------------------------------------------------------------------

@_light
def plot_cost(contracted, ax=None, title: str = ""):
    """Fixed cost and purchases of a selection, stacked."""
    ax = ax or plt.subplots(figsize=(4, 3.4))[1]
    purchase = sel.assign(contracted)
    fixed, bought = sel.fixed_cost(contracted), sel.purchase_cost(purchase)
    ax.bar([0], [bought], color=PURCHASE, width=0.5, label="purchases")
    ax.bar([0], [fixed], bottom=[bought], color=FIXED, width=0.5, label="fixed costs")
    ax.text(0, bought / 2, f"{bought:,.0f}", color="white", ha="center", va="center")
    ax.text(0.27, bought + fixed / 2, f"fixed {fixed:,.0f}", ha="left", va="center", fontsize=8)
    ax.text(0, bought + fixed + 30, f"{bought + fixed:,.0f}", ha="center", va="bottom", weight="bold")
    ax.set_xticks([0], [sel.label(contracted)])
    ax.set_xlim(-0.6, 0.9)
    ax.set_ylim(0, 3000)
    ax.set_ylabel("k€/year")
    ax.legend(fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False, ncol=2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(title, fontsize=10, pad=24)
    return ax


def _selection_summary(contracted) -> None:
    purchase = sel.assign(contracted)
    _display(_purchase_table(purchase))
    print(f"Contracted: {sel.label(contracted)}")
    print(f"Purchases {_k(sel.purchase_cost(purchase))} + fixed costs {_k(sel.fixed_cost(contracted))} "
          f"= {_k(sel.cost(contracted))}")


def buyer_rule() -> tuple:
    """§4: for each component, the cheapest acceptable supplier."""
    rule = sel.buyer_rule()
    contracted = sel.contracted_by(rule)
    print("The buyer's rule: for each component, the cheapest acceptable supplier.")
    _selection_summary(contracted)
    print()
    only_e = ("E",)
    print(f"Everything from the distributor E: {_k(sel.cost(only_e))}, "
          f"{_k(sel.cost(contracted) - sel.cost(only_e))} less than the rule. "
          "E is the cheapest for no component, so the rule never chooses it.")
    return contracted


@_light
def check_selection(suppliers) -> float | None:
    """The cost of the suppliers chosen in the form, or which components are left
    without a supplier."""
    contracted = sel.selection(suppliers)
    if not contracted:
        print("Choose at least one supplier.")
        return None
    if "F" in contracted:
        print("F is not acceptable (score below 6): it is left out.")
        contracted = tuple(s for s in contracted if s != "F")
    missing = sel.uncovered(contracted)
    if missing:
        print(f"Not valid: no contracted supplier offers {', '.join(missing)}.")
        return None
    _selection_summary(contracted)
    rule = sel.contracted_by(sel.buyer_rule())
    difference = sel.cost(contracted) - sel.cost(rule)
    print(f"Against the buyer's rule ({_k(sel.cost(rule))}): "
          + (f"{_k(-difference)} less." if difference < 0 else
             "the same." if difference == 0 else f"{_k(difference)} more."))
    plot_cost(contracted, title="Annual cost of the selection")
    plt.show()
    return sel.cost(contracted)


# ---------------------------------------------------------------------------
# §5 The number of selections and the optimum of the model
# ---------------------------------------------------------------------------

def selections_table() -> pd.DataFrame:
    """Table 4: the 21 selections that cover every component, from the cheapest."""
    optima = set(ls.local_optima(sel.covering_selections()))
    rows = []
    for rank, s in enumerate(sel.covering_selections(), start=1):
        purchase = sel.assign(s)
        rows.append({"Selection": sel.label(s), "Suppliers": len(s),
                     "Purchases (k€/year)": sel.purchase_cost(purchase),
                     "Fixed costs (k€/year)": sel.fixed_cost(s),
                     "Annual cost (k€/year)": sel.cost(s),
                     "Local optimum": "yes" if s in optima else ""})
    return pd.DataFrame(rows, index=pd.RangeIndex(1, len(rows) + 1, name="Rank"))


def count_selections() -> pd.DataFrame:
    """§5: 31 sets of suppliers, 21 of them cover every component; and how 2^n grows."""
    n = len(sel.ACCEPTABLE)
    print(f"With {n} acceptable suppliers there are 2^{n} − 1 = {len(sel.all_selections())} sets of "
          f"contracted suppliers; {len(sel.covering_selections())} of them cover the six components.")
    _display(pd.DataFrame({"Suppliers": [5, 10, 20, 60],
                           "Sets of suppliers (2^n − 1)": [f"{2 ** k - 1:,}" if k < 40 else f"{2 ** k - 1:.2e}"
                                                           for k in (5, 10, 20, 60)]}).set_index("Suppliers"))
    return selections_table()


def solve_model() -> tuple:
    """§5: the optimum of the integer model, against the buyer's rule."""
    solution = mo.solve()
    best = mo.contracted(solution)
    rule = sel.contracted_by(sel.buyer_rule())
    print(f"The model has {solution['variables']} binary variables "
          f"({len(sel.ACCEPTABLE)} y and {solution['variables'] - len(sel.ACCEPTABLE)} x).")
    print("Optimum of the model (PuLP + HiGHS):")
    _display(_purchase_table(mo.purchase(solution)))
    print(f"Contracted: {sel.label(best)}. Annual cost: {_k(solution['cost'])}, "
          f"{_k(sel.cost(rule) - solution['cost'])} less than the buyer's rule.")
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.6), sharey=True)
    plot_cost(rule, ax=axes[0], title="Buyer's rule")
    plot_cost(best, ax=axes[1], title="Model")
    plt.show()
    return best


# ---------------------------------------------------------------------------
# §6 Local search
# ---------------------------------------------------------------------------

def neighbours_table(contracted) -> pd.DataFrame:
    """Every allowed move from a selection, from the cheapest."""
    rows = [{"Move": move, "New selection": sel.label(new), "Annual cost (k€/year)": sel.cost(new)}
            for move, new in ls.neighbours(contracted)]
    return pd.DataFrame(rows).sort_values("Annual cost (k€/year)", kind="stable").reset_index(drop=True)


@_light
def local_search_steps(suppliers) -> tuple | None:
    """§6: the local search from the suppliers chosen in the form, step by step."""
    start = tuple(s for s in sel.selection(suppliers) if s != "F")
    if not start:
        print("Choose at least one acceptable supplier.")
        return None
    missing = sel.uncovered(start)
    if missing:
        print(f"The search must start from a valid selection: no supplier of {sel.label(start)} "
              f"offers {', '.join(missing)}.")
        return None
    steps = ls.search(start)
    for row in steps:
        current = row["selection"]
        print(f"Step {row['step']}: {row['move']} → {sel.label(current)}, {_k(row['cost'])}")
    current = steps[-1]["selection"]
    print()
    print(f"No move lowers the cost of {sel.label(current)}: it is a local optimum. "
          "Its neighbours, from the cheapest:")
    _display(neighbours_table(current))
    for move, missing in ls.blocked(current):
        print(f"  Not allowed: {move} leaves {', '.join(missing)} without a supplier.")
    optimum = sel.covering_selections()[0]
    if current == optimum:
        print(f"{sel.label(current)} is also the optimum of the model.")
    else:
        print(f"The optimum of the model is {sel.label(optimum)}, {_k(sel.cost(optimum))}: "
              f"the search stopped {_k(sel.cost(current) - sel.cost(optimum))} above it.")
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.plot([r["step"] for r in steps], [r["cost"] for r in steps], marker="o")
    for r in steps:
        ax.annotate(sel.label(r["selection"]), (r["step"], r["cost"]), xytext=(6, 6),
                    textcoords="offset points", fontsize=8)
    ax.axhline(sel.cost(optimum), color=BEST, ls=":", label=f"optimum of the model ({sel.cost(optimum):,.0f})")
    ax.set_xticks([r["step"] for r in steps])
    ax.set_xlabel("Step")
    ax.set_ylabel("Annual cost (k€/year)")
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()
    return current


# ---------------------------------------------------------------------------
# §7 Reduced version: relaxation, rounding and branch and bound
# ---------------------------------------------------------------------------

def reduced_data() -> None:
    """The reduced version: suppliers A, B, C and three components."""
    _display(pd.DataFrame({s: {m: c[s].get(m, "–") for m in REDUCED_M} for s in REDUCED_S})
             .T.rename_axis("Annual cost (k€/year)"))
    rows = {}
    for s in sel.all_selections(REDUCED_S):
        value = sel.cost(s, REDUCED_M)
        rows[sel.label(s)] = {"Annual cost (k€/year)": value if value is not None else "does not cover"}
    _display(pd.DataFrame(rows).T.rename_axis("Selection"))


def relaxation() -> None:
    """The linear relaxation of the reduced version and its rounding."""
    r = mo.solve(REDUCED_S, REDUCED_M, "pair", relax=True)
    print("Linear relaxation (every variable between 0 and 1), one constraint per supplier and component:")
    print("  y = " + ", ".join(f"{s} {v:g}" for s, v in r["y"].items()))
    print("  x = " + ", ".join(f"{s}-{m} {v:g}" for (s, m), v in r["x"].items()))
    print(f"  Bound: {r['cost']:,.1f} k€/year. No selection can cost less.")
    up, down = mo.rounded(r, up=True), mo.rounded(r, up=False)
    print(f"Rounding up: {sel.label(up)}, {_k(sel.cost(up, REDUCED_M))} (valid, not optimal).")
    print(f"Rounding down: {sel.label(down)} contracted (not valid).")


def tree_table(nodes: list[dict]) -> pd.DataFrame:
    """One row per node of a branch-and-bound tree (Tables 6 and 7)."""
    rows = []
    for n in nodes:
        rows.append({
            "Node": n["node"],
            "Fixed": ", ".join(f"y_{s} = {v}" for s, v in n["fixed"].items()) or "—",
            "Bound (k€/year)": "—" if n["bound"] is None else f"{n['bound']:,.1f}",
            "y_A, y_B, y_C": "—" if n["y"] is None else ", ".join(f"{abs(v):g}" for v in n["y"].values()),
            "Outcome": n["outcome"] + (f" ({', '.join(n['uncovered'])} without a supplier)"
                                       if n.get("uncovered") else ""),
        })
    return pd.DataFrame(rows).set_index("Node")


@_light
def plot_tree(nodes: list[dict], ax=None, title: str = ""):
    """The branch-and-bound tree: one box per node, numbered in the order solved."""
    ax = ax or plt.subplots(figsize=(7, 4))[1]
    children = {n["node"]: [] for n in nodes}
    parent_of = {}
    by_fixed = {tuple(n["fixed"].items()): n["node"] for n in nodes}
    for n in nodes:
        items = tuple(n["fixed"].items())
        if items:
            parent = by_fixed[items[:-1]]
            children[parent].append(n["node"])
            parent_of[n["node"]] = parent
    x, depth, leaf = {}, {0: 0}, [0]

    def place(node):
        for child in children[node]:
            depth[child] = depth[node] + 1
            place(child)
        if children[node]:
            x[node] = sum(x[ch] for ch in children[node]) / len(children[node])
        else:
            x[node] = leaf[0]
            leaf[0] += 1
    place(0)
    for node, parent in parent_of.items():
        ax.plot([x[parent], x[node]], [-depth[parent], -depth[node]], color="0.6", zorder=1)
        s, v = list(nodes[node]["fixed"].items())[-1]
        ax.text((x[parent] + x[node]) / 2, -(depth[parent] + depth[node]) / 2, f"y_{s}={v}",
                fontsize=7, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.5))
    colours = {"branch": "0.85", "integer": "#b7e4b7", "closed": "#f6d5a8", "no solution": "#f4b6b6"}
    for n in nodes:
        kind = next(k for k in colours if n["outcome"].startswith(k))
        bound = "no solution" if n["bound"] is None else f"{n['bound']:,.1f}"
        ax.text(x[n["node"]], -depth[n["node"]], f"{n['node']}\n{bound}", ha="center", va="center",
                fontsize=8, bbox=dict(boxstyle="round", fc=colours[kind], ec="0.4"), zorder=2)
    for k, colour in colours.items():
        ax.scatter([], [], marker="s", s=80, color=colour, label={"branch": "branched", "integer": "integer",
                                                                  "closed": "closed by the bound",
                                                                  "no solution": "no solution"}[k])
    ax.legend(fontsize=7, loc="lower left", frameon=False)
    ax.set_xlim(-0.8, max(leaf[0] - 0.2, 1.8))
    ax.set_ylim(-max(depth.values()) - 0.6, 0.6)
    ax.axis("off")
    ax.set_title(title, fontsize=10)
    return ax


@_light
def branch_and_bound() -> None:
    """The two branch-and-bound trees of the reduced version, one per way of
    writing "bought from implies contracted"."""
    titles = {"pair": "One constraint per supplier and component: x[s,m] ≤ y[s]",
              "supplier": "One constraint per supplier: Σ x[s,m] ≤ n[s] y[s]"}
    for formulation in mo.FORMULATIONS:
        nodes = mo.branch_and_bound(REDUCED_S, REDUCED_M, formulation)
        best = mo.best_of(nodes)
        print(f"{titles[formulation]}: {len(nodes)} nodes. "
              f"Optimum {sel.label(best['selection'])}, {_k(best['bound'])}.")
        _display(tree_table(nodes))
        plot_tree(nodes, title=titles[formulation])
        plt.show()
