"""What the notebook shows: tables, figures and short messages.

Each function answers one step of the notebook, so that its cells only need
one line of code.
"""

from __future__ import annotations

import functools

import matplotlib.pyplot as plt
import pandas as pd

from . import model as m
from .data import (AIRCRAFT, CHANGE_COST, CHANGE_DEMAND, CHANGE_PRODUCT, FARES, INCLUDES,
                   OFFER_TRIP, SEATS, TRIPS, USES, C, D, L, P, a, r)

ESTIMATE = "tab:red"

# The nine fares of the trips by name, as the notebook writes them in its drop-down list
LABELS = {f"{trip} {fare}": (trip, fare) for trip, fare in P}


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
    """A number with a comma for thousands and no trailing zeros: 41,235; 307.5."""
    text = f"{x:,.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _signed(x: float) -> str:
    return ("+" if x > 0 else "") + _num(x)


def _euros(x: float) -> str:
    return f"{_num(x)} €"


def _grid(values: dict, name: str) -> pd.DataFrame:
    """A table with one row per trip and one column per fare."""
    return pd.DataFrame({fare: {trip: values[trip, fare] for trip in TRIPS} for fare in FARES}).rename_axis(name)


def _seats_text(seats: dict, capacity: dict = C) -> str:
    return "; ".join(f"{l}: {_num(seats[l])} of {_num(capacity[l])} seats" for l in L)


def _range_text(low, high) -> str:
    low_text = "no lower limit" if low is None else _num(low)
    high_text = "no upper limit" if high is None else _num(high)
    return f"{low_text} to {high_text}"


def _product(product) -> tuple:
    """The fare of a trip as a pair (trip, fare), from the pair itself or from its name
    in the drop-down list of the notebook."""
    if isinstance(product, str):
        if product not in LABELS:
            raise ValueError(f"The fare of the trip must be one of {', '.join(LABELS)}.")
        return LABELS[product]
    return tuple(product)


def _changed_table(changed: dict, before: str, after: str) -> None:
    """The fares of the trips whose tickets change between two plans."""
    _display(pd.DataFrame([{"Trip": p[0], "Fare": p[1], before: _num(old), after: _num(new)}
                           for p, (old, new) in changed.items()]).set_index(["Trip", "Fare"]))


# ---------------------------------------------------------------------------
# §1 Data
# ---------------------------------------------------------------------------

def show_data() -> None:
    """Tables 1 and 2: the flights and the nine fares of the trips, with the flights each
    trip uses."""
    _display(pd.DataFrame({l: {"Aircraft": AIRCRAFT[l], "Seats of the aircraft": C[l]} for l in L})
             .T.rename_axis("Flight"))
    rows = []
    for trip, fare in P:
        rows.append({"Trip": trip, "Fare": fare, "Flights used": " and ".join(USES[trip]),
                     "Price (€/ticket)": r[trip, fare], "Forecast demand (tickets)": D[trip, fare],
                     "Seats per ticket on each flight": _num(SEATS[fare])})
    _display(pd.DataFrame(rows).set_index(["Trip", "Fare"]))
    _display(pd.DataFrame({f: {"What it includes": INCLUDES[f]} for f in FARES}).T.rename_axis("Fare"))


# ---------------------------------------------------------------------------
# §2 Model and optimal plan
# ---------------------------------------------------------------------------

def optimal_plan() -> dict:
    """Table 3: the optimal plan; Table 4: binding constraints and slack."""
    solution = m.solve()
    print(f"Optimal plan: revenue {_euros(solution['revenue'])}. Seats used: {_seats_text(solution['seats'])}.")
    _display(_grid({p: _num(solution["plan"][p]) for p in P}, "Tickets on sale"))
    rows = []
    for l in L:
        rows.append({"Constraint": f"Seats of {l}", "Used by the plan": f"{_num(solution['seats'][l])} seats",
                     "Right-hand side": f"{_num(C[l])} seats",
                     "Binding": "yes" if solution["spare seats"][l] < m.TOL else "no",
                     "Slack": f"{_num(solution['spare seats'][l])} seats"})
    for p in P:
        rows.append({"Constraint": f"Demand of {p[0]} {p[1]}", "Used by the plan": f"{_num(solution['plan'][p])} tickets",
                     "Right-hand side": f"{_num(D[p])} tickets",
                     "Binding": "yes" if solution["unsold demand"][p] < m.TOL else "no",
                     "Slack": f"{_num(solution['unsold demand'][p])} tickets"})
    _display(pd.DataFrame(rows).set_index("Constraint"))
    return solution


# ---------------------------------------------------------------------------
# §3 Bid prices
# ---------------------------------------------------------------------------

def bid_prices(flight: str = "RIX → HEL") -> None:
    """Table 5: the bid price of each flight, and the chosen one checked by solving
    again with one seat more and one seat less; Table 6: the fares of the trips whose
    tickets change with that seat; Table 7: the bid price of the ticket of each fare of
    each trip against its price, and the shadow price of its demand; Table 8: the seats
    of the aircraft for which the bid price of each flight holds."""
    if flight not in L:
        raise ValueError(f"The flight must be one of {', '.join(L)}.")
    solution = m.solve()
    bid = solution["bid price"]
    _display(pd.DataFrame({l: {"Seats of the aircraft": C[l], "Bid price (€/seat)": _num(bid[l])} for l in L})
             .T.rename_axis("Flight"))
    up, down = m.change_capacity(flight, 1), m.change_capacity(flight, -1)
    print(f"{flight}: with {C[flight] + 1} seats the revenue changes by {_signed(up)} €; "
          f"with {C[flight] - 1} seats, by {_signed(down)} €. Bid price: {_num(bid[flight])} €/seat.")
    rows = m.seat_change(flight)
    print(f"Fares of the trips whose tickets change with one seat less and one seat more on {flight}:")
    _display(pd.DataFrame([{"Trip": row["product"][0], "Fare": row["product"][1],
                            f"{C[flight] - 1} seats (tickets)": _num(row["less"]),
                            f"{C[flight]} seats, optimal plan (tickets)": _num(row["plan"]),
                            f"{C[flight] + 1} seats (tickets)": _num(row["more"]),
                            "Change with one seat more (€)": _signed(row["change"])} for row in rows])
             .set_index(["Trip", "Fare"]))
    print(f"Total with one seat more: {_signed(sum(row['change'] for row in rows))} €, the bid price of {flight}.")
    rows = []
    for p in P:
        product_bid = m.product_bid_price(p, bid)
        terms = " + ".join(f"{_num(a(p, l))} × {_num(bid[l])}" for l in L if a(p, l) > 0)
        rows.append({"Trip": p[0], "Fare": p[1], "Price (€/ticket)": r[p],
                     "Bid price of the ticket (€/ticket)": f"{terms} = {_num(product_bid)}",
                     "Price − bid price (€/ticket)": _num(r[p] - product_bid),
                     "Shadow price of the demand (€/ticket)": _num(solution["demand price"][p])})
    _display(pd.DataFrame(rows).set_index(["Trip", "Fare"]))
    print("Seats of the aircraft for which the bid price of each flight holds:")
    _display(pd.DataFrame([{"Flight": l, "Seats of the aircraft": _num(C[l]),
                            "Bid price (€/seat)": _num(bid[l]),
                            "Range of the seats": _range_text(*m.validity_range("seats", l))} for l in L])
             .set_index("Flight"))


# ---------------------------------------------------------------------------
# §4 Offer of a tour operator
# ---------------------------------------------------------------------------

@_light
def tour_operator_offer(seats: int = 10, price: float = 120) -> dict | None:
    """An offer of seats BCN–HEL at price €/seat on top of the forecast demand: the
    estimate with the bid prices against the change found by solving again, seat by
    seat, and the plan with the offer."""
    result = m.offer(seats, price)
    if result is None:
        print(f"{seats} seats {OFFER_TRIP} do not fit in the flights: the model has no solution.")
        return None
    bid = result["trip bid price"]
    print(f"Bid price of a seat {OFFER_TRIP}: {' + '.join(_num(result['base']['bid price'][l]) for l in USES[OFFER_TRIP])}"
          f" = {_num(bid)} €/seat.")
    print(f"Estimate with the bid prices: {seats} × ({_num(price)} − {_num(bid)}) = {_signed(result['estimate'])} €.")
    print(f"Solving again with the {seats} seats in the plan: {_signed(result['change'])} €.")
    print("Bid prices with the offer in the plan: "
          + "; ".join(f"{l} {_num(result['new']['bid price'][l])} €/seat" for l in L) + ".")
    changed = m.changed_tickets(result["base"]["plan"], result["new"]["plan"])
    if changed:
        _changed_table(changed, "Without the offer (tickets)", "With the offer (tickets)")

    counts = list(range(0, seats + 1))
    changes = [0.0] + [m.offer(k, price)["change"] for k in counts[1:]]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.plot(counts, [k * (price - bid) for k in counts], color=ESTIMATE, ls="--",
            label=f"estimate: seats × ({_num(price)} − {_num(bid)})")
    ax.plot(counts, changes, color="black", marker="o", ms=4, label="solving again")
    ax.axhline(0, color="0.6", lw=0.8)
    ax.set_xlabel(f"Seats {OFFER_TRIP} of the offer")
    ax.set_ylabel("Change in revenue (€)")
    ax.legend(fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()
    return result


# ---------------------------------------------------------------------------
# §5 Change in the forecast demand of a fare
# ---------------------------------------------------------------------------

def demand_change(product=CHANGE_PRODUCT, new_demand: float = CHANGE_DEMAND,
                  cost: float = CHANGE_COST) -> dict:
    """Table 10: the shadow price of the demand of each fare of each trip and the range
    of the demand for which it holds; then, for the chosen fare of the chosen trip and a
    new forecast demand: the estimate with the shadow price against the change found by
    solving again, the bid prices with the new demand, Table 11 with the fares of the
    trips whose tickets change, and the net result after the cost of the change."""
    p = _product(product)
    _display(pd.DataFrame([{"Trip": q[0], "Fare": q[1], "Forecast demand (tickets)": _num(D[q]),
                            "Shadow price of the demand (€/ticket)": _num(price),
                            "Range of the demand (tickets)": _range_text(*m.validity_range("demand", q))}
                           for q, price in m.solve()["demand price"].items()]).set_index(["Trip", "Fare"]))
    result = m.demand_change(p, new_demand, cost)
    low, high = result["range"]
    where = "inside" if result["inside"] else "outside"
    print(f"{p[0]} {p[1]}: forecast demand {_num(D[p])} tickets, shadow price of its demand "
          f"{_num(result['shadow price'])} €/ticket, which holds for a demand of "
          f"{_range_text(low, high)} tickets.")
    print(f"With {_num(new_demand)} tickets of forecast demand ({_signed(new_demand - D[p])} tickets): "
          f"revenue {_euros(result['new']['revenue'])} instead of {_euros(result['base']['revenue'])}.")
    print(f"Estimate with the shadow price: {_num(result['shadow price'])} €/ticket × "
          f"({_num(new_demand)} − {_num(D[p])}) tickets = {_signed(result['estimate'])} €. "
          f"Solving again: {_signed(result['change'])} €.")
    print(f"{_num(new_demand)} tickets is {where} the range of the shadow price.")
    print("Bid prices with the new demand: "
          + "; ".join(f"{l} {_num(result['new']['bid price'][l])} €/seat" for l in L) + ".")
    if result["changed"]:
        print("Fares of the trips whose tickets change:")
        _changed_table(result["changed"], f"{_num(D[p])} tickets of demand",
                       f"{_num(new_demand)} tickets of demand")
    print(f"Cost of the change: {_euros(cost)}. Net result: {_signed(result['change'])} − "
          f"({_signed(cost)}) = {_signed(result['net'])} €; with the estimate it would be "
          f"{_signed(result['net estimate'])} €.")
    return result
