"""What the notebook shows: tables, figures and short messages.

Each function answers one step of the notebook, so that its cells only need
one line of code.
"""

from __future__ import annotations

import functools

import matplotlib.pyplot as plt
import pandas as pd

from . import model as m
from .data import CURVE, INCLUDES, C, D, F, a, r

COLOURS = {"Business": "tab:blue", "Economy FLEX": "tab:orange", "Economy BASIC": "tab:purple"}
RANGE = "tab:green"
ESTIMATE = "tab:red"

# Constraints as the drop-down list of the notebook names them
CONSTRAINTS = {m.name(key): key for key in m.KEYS}


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


def _num(x: float) -> str:
    """A number with a comma for thousands and no trailing zeros: 36,480; 307.5; 66.67."""
    text = f"{x:,.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _euros(x: float) -> str:
    return f"{_num(x)} €"


def _unit(key: str) -> str:
    return "seat" if key == m.CAPACITY else "ticket"


def _range_text(low, high) -> str:
    if high is None:
        return f"{_num(low)} or more"
    return f"{_num(low)} to {_num(high)}"


# ---------------------------------------------------------------------------
# §1 Data
# ---------------------------------------------------------------------------

def show_data() -> None:
    """Table 1: the fares, with the revenue per seat of each one."""
    print(f"Capacity of the cabin: {C} seats. Prices of a one-way ticket.")
    _display(pd.DataFrame({f: {"What it includes": INCLUDES[f], "Price (€/ticket)": r[f],
                               "Seats per ticket": _num(a[f]), "Forecast demand (tickets)": D[f],
                               "Revenue per seat (€/seat)": _num(r[f] / a[f])} for f in F})
             .T.rename_axis("Fare"))


# ---------------------------------------------------------------------------
# §3 Optimal plan and binding constraints
# ---------------------------------------------------------------------------

def _plan_table(solution: dict) -> pd.DataFrame:
    rows = {f: {"Tickets on sale": _num(solution["plan"][f]), "Forecast demand (tickets)": D[f],
                "Seats used": _num(a[f] * solution["plan"][f]),
                "Revenue (€)": _num(r[f] * solution["plan"][f])} for f in F}
    rows["Total"] = {"Tickets on sale": _num(sum(solution["plan"].values())), "Forecast demand (tickets)": "",
                     "Seats used": _num(solution["seats"]), "Revenue (€)": _num(solution["revenue"])}
    return pd.DataFrame(rows).T.rename_axis("Fare")


def optimal_plan() -> dict:
    """Table 2: the optimal plan; Table 3: which constraints are binding and the
    slack of the others."""
    solution = m.solve()
    print(f"Optimal plan: revenue {_euros(solution['revenue'])}, "
          f"{_num(solution['seats'])} of {C} seats used.")
    _display(_plan_table(solution))
    rows = []
    for key in m.KEYS:
        left = solution["seats"] if key == m.CAPACITY else solution["plan"][key]
        unit = "seats" if key == m.CAPACITY else "tickets"
        gap = m.slack(solution, key)
        rows.append({"Constraint": m.name(key), "Used by the plan": f"{_num(left)} {unit}",
                     "Right-hand side": f"{_num(m.rhs(key))} {unit}",
                     "Binding": "yes" if abs(gap) < m.TOL else "no", "Slack": f"{_num(gap)} {unit}"})
    _display(pd.DataFrame(rows).set_index("Constraint"))
    return solution


# ---------------------------------------------------------------------------
# §4 Shadow prices, checked by solving again
# ---------------------------------------------------------------------------

def shadow_prices(constraint: str = "Capacity of the cabin") -> None:
    """Table 4: the shadow price of each constraint; then the chosen constraint is
    checked by solving the model again with one more unit of its right-hand side."""
    if constraint not in CONSTRAINTS:
        raise ValueError(f"The constraint must be one of {', '.join(CONSTRAINTS)}.")
    solution = m.solve()
    _display(pd.DataFrame([{"Constraint": m.name(key), "Right-hand side": f"{_num(m.rhs(key))} {_unit(key)}s",
                            "Shadow price": f"{_num(m.shadow_price(solution, key))} €/{_unit(key)}"}
                           for key in m.KEYS]).set_index("Constraint"))
    key = CONSTRAINTS[constraint]
    check = m.one_more(key)
    unit = "seats" if key == m.CAPACITY else "tickets"
    print(f"{constraint}: {_num(m.rhs(key))} {unit} → {_num(m.rhs(key) + 1)} {unit}.")
    print(f"Revenue: {_euros(check['revenue'])} → {_euros(check['revenue with one more'])}, "
          f"a change of {_euros(check['change'])}.")
    print(f"Shadow price: {_num(check['shadow price'])} €/{_unit(key)}.")


# ---------------------------------------------------------------------------
# §5 and §6 Ranges and revenue against capacity
# ---------------------------------------------------------------------------

def _draw_curve(ax, curve) -> None:
    ax.plot([k for k, _ in curve], [z for _, z in curve], color="black", lw=1.8, label="optimal revenue")
    ax.set_xlim(CURVE[0], CURVE[1])
    ax.set_ylim(0, max(z for _, z in curve) * 1.12)
    ax.set_xlabel("Capacity of the cabin (seats)")
    ax.set_ylabel("Revenue (€)")
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:,.0f}")
    ax.spines[["top", "right"]].set_visible(False)


@_light
def revenue_against_capacity() -> None:
    """Figure and Tables 5 and 6: the revenue for every capacity from 0 to 320 seats,
    the slope of each piece, the points where it changes and the range of the bid
    price; then the range of every shadow price."""
    curve = m.revenue_curve()
    pieces = m.segments()
    low, high = m.validity_range(m.CAPACITY)
    revenue = dict(curve)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.axvspan(low, high, color=RANGE, alpha=0.12, label=f"range of the bid price: {_range_text(low, high)} seats")
    _draw_curve(ax, curve)
    for piece in pieces:
        middle = (piece["from"] + piece["to"]) / 2
        last = piece is pieces[-1]
        ax.annotate(f"{_num(piece['slope'])} €/seat", (middle, revenue[round(middle)]),
                    xytext=(0, 6) if last else (6, -16), textcoords="offset points",
                    ha="center" if last else "left", fontsize=8, weight="bold")
    for piece in pieces[1:]:
        k = piece["from"]
        ax.axvline(k, color="0.6", ls=":", lw=1)
        ax.annotate(f"{k}", (k, 0), xytext=(3, 4), textcoords="offset points", fontsize=8, color="0.3")
    ax.scatter([C], [revenue[C]], s=60, color=RANGE, zorder=3)
    ax.annotate(f"{C} seats\n{_euros(revenue[C])}", (C, revenue[C]), xytext=(-8, 10),
                textcoords="offset points", ha="right", fontsize=8)
    ax.legend(fontsize=8, loc="upper left", frameon=False)
    plt.show()

    _display(pd.DataFrame([{"From (seats)": p["from"], "To (seats)": p["to"],
                            "Slope (€/seat)": _num(p["slope"]),
                            "Fare that takes the extra seats": p["fare"] or "none: the seats stay empty"}
                           for p in pieces], index=range(1, len(pieces) + 1)).rename_axis("Piece"))
    solution = m.solve()
    rows = []
    for key in m.KEYS:
        unit = "seats" if key == m.CAPACITY else "tickets"
        rows.append({"Constraint": m.name(key), "Right-hand side": f"{_num(m.rhs(key))} {unit}",
                     "Shadow price": f"{_num(m.shadow_price(solution, key))} €/{_unit(key)}",
                     "Holds from … to …": f"{_range_text(*m.validity_range(key))} {unit}"})
    _display(pd.DataFrame(rows).set_index("Constraint"))


# ---------------------------------------------------------------------------
# §7 Another capacity
# ---------------------------------------------------------------------------

@_light
def other_capacity(seats: float = 180) -> dict:
    """The plan with another capacity, the change in revenue against 220 seats found
    by solving again, and the change estimated with the bid price."""
    result = m.other_capacity(seats)
    base, new = result["base"], result["new"]
    low, high = result["range"]
    table = pd.DataFrame({f"{C} seats": {f: _num(base["plan"][f]) for f in F},
                          f"{_num(seats)} seats": {f: _num(new["plan"][f]) for f in F}})
    table.loc["Revenue (€)"] = [_num(base["revenue"]), _num(new["revenue"])]
    _display(table.rename_axis("Tickets on sale"))
    where = "inside" if result["inside"] else "outside"
    print(f"Change in revenue, solving again: {_euros(result['change'])}.")
    print(f"Estimate with the bid price: {_num(base['bid price'])} €/seat × ({_num(seats)} − {C}) seats "
          f"= {_euros(result['estimate'])}.")
    print(f"{_num(seats)} seats is {where} the range of the bid price ({_range_text(low, high)} seats). "
          f"Difference between the change and the estimate: {_euros(result['change'] - result['estimate'])}.")

    curve = m.revenue_curve()
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.axvspan(low, high, color=RANGE, alpha=0.12, label=f"range of the bid price: {_range_text(low, high)} seats")
    _draw_curve(ax, curve)
    xs = [CURVE[0], CURVE[1]]
    ax.plot(xs, [base["revenue"] + base["bid price"] * (k - C) for k in xs], color=ESTIMATE, ls="--", lw=1.2,
            label=f"estimate with the bid price: {_num(base['bid price'])} €/seat from {C} seats")
    ax.scatter([C], [base["revenue"]], s=60, color=RANGE, zorder=3)
    ax.scatter([seats], [new["revenue"]], s=60, color="black", zorder=3)
    ax.scatter([seats], [base["revenue"] + result["estimate"]], s=60, facecolor="none", edgecolor=ESTIMATE,
               lw=1.5, zorder=3)
    ax.annotate(f"{_num(seats)} seats\n{_euros(new['revenue'])}", (seats, new["revenue"]), xytext=(8, -26),
                textcoords="offset points", fontsize=8)
    ax.legend(fontsize=8, loc="upper left", frameon=False)
    plt.show()
    return result
