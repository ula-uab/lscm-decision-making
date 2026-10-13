"""What the notebook shows: tables, figures and short messages.

Each function answers one step of the notebook, so that its cells only need
one line of code.
"""

from __future__ import annotations

import functools

import matplotlib.pyplot as plt
import pandas as pd

from . import model as m
from .data import AIRCRAFT, FARES, INCLUDES, OFFER_TRIP, SEATS, TRIPS, USES, C, D, L, P, a, r

COLOURS = {"rule": "tab:orange", "model": "tab:blue"}
ESTIMATE = "tab:red"


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
# §2 The rule «highest fare first»
# ---------------------------------------------------------------------------

def rule() -> dict:
    """Table 3: the plan of the rule, its revenue and the seats it uses on each flight."""
    result = m.highest_fare_first()
    print("Order of the rule, from the highest price to the lowest:")
    print("  " + "; ".join(f"{trip} {fare} {r[trip, fare]} €" for trip, fare in result["order"]))
    print(f"Revenue of the rule: {_euros(result['revenue'])}. Seats used: {_seats_text(result['seats'])}.")
    _display(_grid({p: f"{_num(result['plan'][p])} of {D[p]}" for p in P}, "Tickets on sale (of the demand)"))
    return result


# ---------------------------------------------------------------------------
# §4 Optimal plan, against the rule
# ---------------------------------------------------------------------------

@_light
def optimal_plan() -> dict:
    """Table 4: the optimal plan next to the plan of the rule, and the difference fare
    by fare and trip by trip; Table 5: binding constraints and slack."""
    solution = m.solve()
    rule_ = m.highest_fare_first()
    gap = solution["revenue"] - rule_["revenue"]
    print(f"Optimal plan: revenue {_euros(solution['revenue'])}. Seats used: {_seats_text(solution['seats'])}.")
    print(f"Rule «highest fare first»: {_euros(rule_['revenue'])}. "
          f"The rule loses {_euros(gap)}, {gap / solution['revenue'] * 100:.1f} % of the optimal revenue.")
    rows = []
    for p in P:
        diff = rule_["plan"][p] - solution["plan"][p]
        rows.append({"Trip": p[0], "Fare": p[1], "Rule (tickets)": _num(rule_["plan"][p]),
                     "Model (tickets)": _num(solution["plan"][p]), "Rule − model (tickets)": _signed(diff),
                     "Rule − model (€)": _signed(r[p] * diff)})
    _display(pd.DataFrame(rows).set_index(["Trip", "Fare"]))

    fig, ax = plt.subplots(figsize=(9, 3.6))
    xs = range(len(P))
    ax.bar([x - 0.2 for x in xs], [rule_["plan"][p] for p in P], width=0.4, color=COLOURS["rule"],
           label="rule «highest fare first»")
    ax.bar([x + 0.2 for x in xs], [solution["plan"][p] for p in P], width=0.4, color=COLOURS["model"],
           label="optimal plan of the model")
    ax.set_xticks(list(xs), [f"{trip}\n{fare.replace('Economy ', '')}" for trip, fare in P], fontsize=8)
    ax.set_ylabel("Tickets on sale")
    ax.legend(fontsize=8, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()

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
# §5 Bid prices
# ---------------------------------------------------------------------------

def bid_prices(flight: str = "RIX → HEL") -> None:
    """Table 6: the bid price of each flight, and the chosen one checked by solving
    again with one seat more and one seat less; Table 7: the fares of the trips whose
    tickets change with that seat; Table 8: the bid price of the ticket of each fare of
    each trip against its price, and the shadow price of its demand."""
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


# ---------------------------------------------------------------------------
# §7 Offer of a tour operator
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
    changed = {p: (result["base"]["plan"][p], result["new"]["plan"][p]) for p in P
               if abs(result["base"]["plan"][p] - result["new"]["plan"][p]) > m.TOL}
    if changed:
        _display(pd.DataFrame([{"Trip": p[0], "Fare": p[1], "Without the offer (tickets)": _num(old),
                                "With the offer (tickets)": _num(new)} for p, (old, new) in changed.items()])
                 .set_index(["Trip", "Fare"]))

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
# §8 Another aircraft
# ---------------------------------------------------------------------------

def other_aircraft(flight: str = "RIX → HEL", seats: float = 180, cost_change: float = 1200) -> dict:
    """Another aircraft on a flight: new plan and revenue, change found by solving again
    against the estimate with the bid price, inside or outside its range, and the net
    result after the change in operating cost."""
    if flight not in L:
        raise ValueError(f"The flight must be one of {', '.join(L)}.")
    result = m.other_aircraft(flight, seats, cost_change)
    base, new = result["base"], result["new"]
    low, high = result["range"]
    where = "inside" if result["inside"] else "outside"
    print(f"{flight} with {_num(seats)} seats instead of {_num(C[flight])}: "
          f"revenue {_euros(new['revenue'])} instead of {_euros(base['revenue'])}.")
    rows = []
    for p in P:
        if abs(base["plan"][p] - new["plan"][p]) > m.TOL:
            rows.append({"Trip": p[0], "Fare": p[1], f"{_num(C[flight])} seats (tickets)": _num(base["plan"][p]),
                         f"{_num(seats)} seats (tickets)": _num(new["plan"][p])})
    if rows:
        print("Fares of the trips whose tickets change:")
        _display(pd.DataFrame(rows).set_index(["Trip", "Fare"]))
    bid = base["bid price"][flight]
    print(f"Change in revenue, solving again: {_signed(result['change'])} €.")
    print(f"Estimate with the bid price: {_num(bid)} €/seat × ({_num(seats)} − {_num(C[flight])}) seats "
          f"= {_signed(result['estimate'])} €.")
    print(f"{_num(seats)} seats is {where} the range of the bid price of {flight} ({_range_text(low, high)} seats).")
    print(f"Change in operating cost: {_signed(cost_change)} €. Net result: {_signed(result['change'])} − "
          f"({_signed(cost_change)}) = {_signed(result['net'])} €; with the estimate it would be "
          f"{_signed(result['net estimate'])} €.")
    return result
