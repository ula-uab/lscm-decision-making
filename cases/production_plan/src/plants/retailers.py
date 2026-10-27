"""M4 · Retailers (retailers.md): the network of distribution_network.md (M3) with
the retailers as a new stage at its end. The retailers receive the orders; of the
demand that a retailer does not receive in its month, the backorder share is
backordered and the rest is lost sales. Written with PuLP and solved with HiGHS;
and what the notebook retailers.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the retailers, their arcs, their orders and backorder shares;
2. ``retailer_plan``: the plan with forecast 5, with the flows of one month;
3. ``backorder_share_test``, ``lost_sale_cost_test``, ``promotion_test`` and
   ``transport_cost_test``: the plan when one datum changes.

The model reuses the list of arcs and the functions ``entering`` and ``leaving``
of M3, and the check of a single optimal plan of M2; M3 does not change.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .central_warehouse import SEVERAL, only_optimal
from .data import (ARCS_M4, BACKORDER_SHARE, CENTRAL, FORECAST_5, F, K, K_h_node, K_h_node_m4, K_n, LOCAL,
                   NODES, NODES_M4, PLACES_M4, RAIL_TERMINAL, RETAILERS, REGIONAL, SHARE_M4, T, b_0, c, c_b,
                   c_h_node_m4, c_l, h_node_0_m4, h_node_end_m4)
from .distribution_network import POSITION, arc_name, entering, leaving
from .model import TOL, _constraints, _optimal
from .show import COLOURS, SHORT, _display, _european_axes, _light, _number

FORECAST = "Forecast 5"                   # M4 is solved with forecast 5
DEMAND = FORECAST_5
FIRST_RETAILER_ARC = len(ARCS_M4) - 12    # arcs 14 to 25 of the list go to the retailers

# Position of each retailer in the figure of the network, and where its label goes
RETAILER_POSITION = {
    "Retailer 1": (0.4, 42.6, "right"), "Retailer 2": (2.0, 43.1, "right"),
    "Retailer 3": (0.3, 38.2, "right"), "Retailer 4": (-1.4, 37.6, "right"),
    "Retailer 5": (-4.0, 38.9, "left"), "Retailer 6": (-3.2, 36.9, "right"),
}


def _key(node: str) -> str:
    return node.replace(" ", "")


def orders(demand: dict = DEMAND, share: dict = SHARE_M4, months=T) -> dict:
    """The orders of each retailer in each month (bikes): its share of the forecast."""
    return {(r, t): share[r] * demand[t] for r in share for t in months}


def build(order: dict | None = None, months=T, arc_list: list = ARCS_M4, backorder_share: dict = BACKORDER_SHARE,
          lost_sale_cost: dict = c_l, holding: dict = c_h_node_m4, storage: dict = K_h_node_m4,
          node_capacity: dict = K_n, initial: dict = h_node_0_m4, final: dict | None = h_node_end_m4,
          backorder_cost: float = c_b, backorders_initial: float = b_0, capacity: dict = K, nodes=NODES_M4,
          plants=F, retailers=RETAILERS):
    """The model of M4, not solved. ``order`` gives the orders of each retailer in
    each month, by (r, t); by default, its share of forecast 5. Returns the model, a
    dict of its variables by kind ("p" by (f, t); "x" by (a, t); "h" by (i, t);
    "s", "b", "l" by (r, t)) and the cost expression."""
    order = order or orders(months=months)
    model = pulp.LpProblem("retailers", pulp.LpMinimize)
    # p = bikes assembled; x = bikes shipped on each arc; h = stock at the end of
    # the month; s = deliveries, b = backorders at the end of the month and
    # l = lost sales of each retailer
    p = {(f, t): model.add_variable(f"p_{_key(f)}_{t}", lowBound=0) for f in plants for t in months}
    x = {(a, t): model.add_variable(f"x_{a}_{t}", lowBound=0) for a in range(len(arc_list)) for t in months}
    h = {(i, t): model.add_variable(f"h_{_key(i)}_{t}", lowBound=0) for i in nodes for t in months}
    s = {(r, t): model.add_variable(f"s_{_key(r)}_{t}", lowBound=0) for r in retailers for t in months}
    b = {(r, t): model.add_variable(f"b_{_key(r)}_{t}", lowBound=0) for r in retailers for t in months}
    l = {(r, t): model.add_variable(f"l_{_key(r)}_{t}", lowBound=0) for r in retailers for t in months}
    # Minimise the assembly, holding, transport, backorder and lost-sale cost
    cost = (pulp.lpSum(c[f] * p[f, t] for f in plants for t in months)
            + pulp.lpSum(holding[i] * h[i, t] for i in nodes for t in months)
            + pulp.lpSum(arc_list[a]["cost"] * x[a, t] for a in range(len(arc_list)) for t in months)
            + pulp.lpSum(backorder_cost * b[r, t] + lost_sale_cost[r] * l[r, t] for r in retailers for t in months))
    model += cost
    for i in nodes:
        into, out = entering(i, arc_list), leaving(i, arc_list)
        for k, t in enumerate(months):
            before = initial[i] if k == 0 else h[i, months[k - 1]]
            assembled = p[i, t] if i in plants else 0
            delivered = s[i, t] if i in retailers else 0
            arriving = pulp.lpSum(x[a, t] for a in into)
            shipped = pulp.lpSum(x[a, t] for a in out)
            # Stock balance at each node
            model += (before + assembled + arriving == shipped + delivered + h[i, t], f"balance_{_key(i)}_{t}")
            # Shipment limit: what leaves is at most the stock of the previous month,
            # plus what the node assembles and what arrives that month
            model += (shipped + delivered <= before + assembled + arriving, f"shipment_limit_{_key(i)}_{t}")
            model += (h[i, t] <= storage[i], f"storage_{_key(i)}_{t}")
            if i in node_capacity:
                model += (arriving <= node_capacity[i], f"node_capacity_{_key(i)}_{t}")
        if final is not None:
            model += (h[i, months[-1]] >= final[i], f"final_stock_{_key(i)}")
    for r in retailers:
        for k, t in enumerate(months):
            before = backorders_initial if k == 0 else b[r, months[k - 1]]
            # Backorder balance, written with the orders on the right: deliveries,
            # backorders at the end of the month and lost sales, less the backorders
            # at the start of the month, equal the orders of the month
            model += (s[r, t] + b[r, t] + l[r, t] - before == order[r, t], f"backorders_{_key(r)}_{t}")
            # Backorder share: from January to May, of the demand not received in the
            # month, the share beta[r] is backordered and the rest is lost sales
            if k < len(months) - 1:
                model += (b[r, t] == backorder_share[r] * (before + order[r, t] - s[r, t]),
                          f"backorder_share_{_key(r)}_{t}")
        # No backorders at the end of June: what is not delivered by then is lost sales
        model += (b[r, months[-1]] == 0, f"backorders_at_the_end_{_key(r)}")
    for a in range(len(arc_list)):
        for t in months:
            model += (x[a, t] <= arc_list[a]["capacity"], f"arc_capacity_{a}_{t}")
    for f in plants:
        for t in months:
            model += (p[f, t] <= capacity[f][t], f"capacity_{_key(f)}_{t}")
    return model, {"p": p, "x": x, "h": h, "s": s, "b": b, "l": l}, cost


def only_plan(**data) -> bool | None:
    """True if the optimal plan of M4 with the data given (the arguments of ``build``)
    is the only one; False if several plans have the optimal cost; None if the
    model has no solution."""
    model, var, cost = build(**data)
    return only_optimal(model, [v for kind in var.values() for v in kind.values()], cost)


def solve(**data) -> dict | None:
    """Solve M4 with the data given (the arguments of ``build``). Returns the cost
    (EUR); the bikes assembled, shipped on each arc and in stock at each node; the
    deliveries, backorders and lost sales of each retailer, by month (bikes); and
    the shadow prices of the arc, node and storage capacities (EUR/bike). None if
    the model has no solution."""
    model, var, _ = build(**data)
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    months = sorted({t for _, t in var["p"]}, key=T.index)
    arc_list = data.get("arc_list", ARCS_M4)
    nodes = data.get("nodes", NODES_M4)
    node_capacity = data.get("node_capacity", K_n)
    cons = _constraints(model)
    clean = lambda v: 0.0 if abs(v) < TOL else v      # noqa: E731  (no "-0.0" in tables)
    values = {kind: {key: clean(v.value()) for key, v in var[kind].items()} for kind in var}
    return {
        "months": months, "arcs": arc_list, "orders": data.get("order") or orders(months=months),
        "cost": pulp.value(model.objective),
        "assembly": values["p"], "flow": values["x"], "stock": values["h"],
        "deliveries": values["s"], "backorders": values["b"], "lost sales": values["l"],
        "arc price": {(a, t): clean(cons[f"arc_capacity_{a}_{t}"].pi) for a in range(len(arc_list)) for t in months},
        "node price": {(i, t): clean(cons[f"node_capacity_{_key(i)}_{t}"].pi) for i in node_capacity for t in months},
        "storage price": {(i, t): clean(cons[f"storage_{_key(i)}_{t}"].pi) for i in nodes for t in months},
    }


def m3_has_no_solution(demand: dict = DEMAND) -> bool:
    """True if M3, with the demand at the local warehouses split as in M3, has no
    solution for a demand."""
    from . import distribution_network
    return distribution_network.solve(demand=demand) is None


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def show_data() -> None:
    """Tables 1 to 3 of retailers.md: the retailers and their places, their arcs, and
    their orders, backorder shares and lost-sale cost."""
    _display(pd.DataFrame({r: {"Place": PLACES_M4[r][0], "Latitude": _number(PLACES_M4[r][1], 4),
                               "Longitude": _number(PLACES_M4[r][2], 4)} for r in RETAILERS}).T.rename_axis("Retailer"))
    _display(pd.DataFrame([{"Arc": a + 1, "Origin": arc["origin"], "Destination": arc["destination"],
                            "Distance (km)": arc["km"], "Transport cost (€/bike)": arc["cost"],
                            "Arc capacity (bikes/month)": arc["capacity"]}
                           for a, arc in enumerate(ARCS_M4) if a >= FIRST_RETAILER_ARC]).set_index("Arc"))
    order = orders()
    table = pd.DataFrame({r: {t: order[r, t] for t in T} for r in RETAILERS}).T
    table.insert(0, "Share", [f"{_number(100 * SHARE_M4[r])} %" for r in RETAILERS])
    table.insert(1, "Backorder share", [_number(BACKORDER_SHARE[r], 1) for r in RETAILERS])
    table.insert(2, "Lost-sale cost (€/bike)", [c_l[r] for r in RETAILERS])
    _display(table.rename_axis("Orders (bikes/month)"))
    print(f"{FORECAST} (bikes/month): " + "; ".join(f"{t} {_number(DEMAND[t])}" for t in T) + ".")


def _retailer_table(solution: dict) -> pd.DataFrame:
    months = solution["months"]
    rows = {}
    for label, key in (("Orders", "orders"), ("Deliveries", "deliveries"),
                       ("Backorders at the end of the month", "backorders"), ("Lost sales", "lost sales")):
        for r in RETAILERS:
            rows[label, f"{r} ({PLACES_M4[r][0]})"] = {t: solution[key][r, t] for t in months}
    return pd.DataFrame(rows).T.rename_axis(["Bikes", "Retailer"])


def _tables(solution: dict) -> None:
    months, arc_list = solution["months"], solution["arcs"]
    _display(pd.DataFrame({t: {f: solution["assembly"][f, t] for f in F} for t in months})
             .rename_axis("Bikes assembled"))
    _display(pd.DataFrame({t: {f"{a + 1}. {arc_name(arc)}": solution["flow"][a, t] for a, arc in enumerate(arc_list)}
                           for t in months}).rename_axis("Flow on each arc (bikes)"))
    _display(pd.DataFrame({t: {i: solution["stock"][i, t] for i in NODES} for t in months})
             .rename_axis("Stock at the end of the month (bikes)"))
    _display(_retailer_table(solution))


def _prices(solution: dict) -> None:
    """The shadow prices of the arc, node and storage capacities that are full in
    some month (negative: a saving)."""
    months, arc_list = solution["months"], solution["arcs"]
    rows = {}
    for a, arc in enumerate(arc_list):
        if any(solution["arc price"][a, t] for t in months):
            rows[f"Arc capacity, {a + 1}. {arc_name(arc)}"] = {t: solution["arc price"][a, t] for t in months}
    for i in sorted({i for i, _ in solution["node price"]}, key=NODES.index):
        if any(solution["node price"][i, t] for t in months):
            rows[f"Node capacity, {i}"] = {t: solution["node price"][i, t] for t in months}
    for i in NODES:
        if i != RAIL_TERMINAL and any(solution["storage price"][i, t] for t in months):
            rows[f"Storage capacity, {i}"] = {t: solution["storage price"][i, t] for t in months}
    if rows:
        print("Shadow price of each capacity that is full in some month (€/bike): the change in cost with one "
              "more bike of capacity (negative: a saving).")
        _display(pd.DataFrame(rows).T.rename_axis("Capacity"))


@_light
def _figure(solution: dict, month: str) -> None:
    """Left: the network with the retailers, with the flow on each arc in one month;
    an arc whose capacity is full is drawn in red. Right: lost sales of each retailer
    in each month."""
    arc_list, months = solution["arcs"], solution["months"]
    position = {**POSITION, **RETAILER_POSITION}
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1.4, 1]})
    lon = {i: position[i][0] for i in NODES_M4}
    lat = {i: position[i][1] for i in NODES_M4}
    top = max([solution["flow"][a, month] for a in range(len(arc_list))] + [1])
    for a, arc in enumerate(arc_list):
        i, j = arc["origin"], arc["destination"]
        flow = solution["flow"][a, month]
        full = flow > TOL and abs(flow - arc["capacity"]) < 1e-6
        colour = SHORT if full else ("0.25" if flow > TOL else "0.85")
        left.annotate("", xy=(lon[j], lat[j]), xytext=(lon[i], lat[i]),
                      arrowprops=dict(arrowstyle="-|>", color=colour, lw=0.8 + 4 * flow / top,
                                      ls="-" if arc["mode"] == "Road" else "--", shrinkA=6, shrinkB=6))
        if flow > TOL:
            left.annotate(_number(flow), ((lon[i] + lon[j]) / 2, (lat[i] + lat[j]) / 2), fontsize=7,
                          color=colour, ha="center", va="center",
                          bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    for i in NODES_M4:
        colour = COLOURS.get(i, "black" if i == RAIL_TERMINAL else ("tab:red" if i in RETAILERS else "tab:gray"))
        marker = "s" if i == RAIL_TERMINAL else ("D" if i in RETAILERS else "o")
        left.scatter(lon[i], lat[i], s=50, color=colour, marker=marker, zorder=3)
        side = position[i][2]
        left.annotate(f"{i}\n{PLACES_M4[i][0]}", (lon[i], lat[i]), xytext=(7 if side == "right" else -7, 0),
                      textcoords="offset points", fontsize=6.5, ha="left" if side == "right" else "right",
                      va="center")
    left.plot([], [], color="0.25", lw=2, label="road")
    left.plot([], [], color="0.25", lw=2, ls="--", label="rail")
    left.plot([], [], color=SHORT, lw=2, label="arc capacity full")
    left.set_title(f"Flow on each arc in {month} (bikes); positions follow the map, not to scale", fontsize=10)
    left.set_xlim(-8.5, 5.5)
    left.set_ylim(36.4, 43.8)
    left.axis("off")
    left.legend(fontsize=7, loc="lower right")

    x = range(len(months))
    bottom = [0.0] * len(months)
    colours = plt.get_cmap("tab10")
    for k, r in enumerate(RETAILERS):
        values = [solution["lost sales"][r, t] for t in months]
        right.bar(x, values, bottom=bottom, color=colours(k), width=0.7, label=f"{r} ({PLACES_M4[r][0]})")
        bottom = [b + v for b, v in zip(bottom, values)]
    right.set_xticks(list(x), months)
    right.set_ylabel("Lost sales (bikes)")
    right.set_ylim(0, max(150, max(bottom) * 1.2))
    right.set_title("Lost sales of each retailer", fontsize=10)
    right.legend(fontsize=7, loc="upper left")
    right.spines[["top", "right"]].set_visible(False)
    _european_axes(fig)
    plt.show()


def _summary(solution: dict) -> None:
    """Lost sales of each retailer and bikes assembled at each plant, in one table each."""
    months = solution["months"]
    _display(pd.DataFrame({t: {f"{r} ({PLACES_M4[r][0]})": solution["lost sales"][r, t] for r in RETAILERS}
                           for t in months}).rename_axis("Lost sales (bikes)"))
    _display(pd.DataFrame({t: {f: solution["assembly"][f, t] for f in F} for t in months})
             .rename_axis("Bikes assembled"))


def _report(data: dict, heading: str, month: str = "May", full: bool = True) -> dict | None:
    """Solve M4 with the data given and show the plan and its cost, whether other
    plans have the same cost, the tables (all of them, or the lost sales and the
    assembly) and the figure."""
    if month not in T:
        raise ValueError(f"The month must be one of {', '.join(T)}.")
    solution = solve(**data)
    if solution is None:
        print(f"{heading}: the model has no solution.")
        return None
    lost = sum(solution["lost sales"].values())
    print(f"{heading}: optimal plan, cost {_number(solution['cost'], 2)} €; lost sales {_number(lost)} bikes.")
    if not only_plan(**data):
        print(SEVERAL)
    if full:
        _tables(solution)
        _prices(solution)
    else:
        _summary(solution)
    _figure(solution, month)
    return solution


def retailer_plan(month: str = "May") -> dict | None:
    """The plan with forecast 5, with the flows of one month on the map; and, first,
    whether M3 has a plan for forecast 5."""
    if m3_has_no_solution():
        ordered = sum(DEMAND[t] for t in T[3:])
        assembled = sum(K[f][t] for f in F for t in T[3:])
        ending = sum(h_node_end_m4[f] for f in F)
        print(f"M3, with the orders at the local warehouses, has no solution with {FORECAST.lower()}: from April "
              f"to June {_number(ordered)} bikes are ordered and the plants can assemble {_number(assembled)}, "
              f"and the plants have to end June with {_number(ending)} bikes. At the end of March "
              f"{_number(ordered - assembled + ending)} bikes have to be in stock, and the network can hold "
              f"{_number(sum(K_h_node[i] for i in NODES))}.")
        print()
    return _report({}, FORECAST, month)


def backorder_share_test(retailer: str = "Retailer 6", backorder_share: float = 0.4) -> dict | None:
    """The plan with forecast 5 and the backorder share of one retailer changed."""
    if retailer not in RETAILERS:
        raise ValueError(f"The retailer must be one of {', '.join(RETAILERS)}.")
    share = {**BACKORDER_SHARE, retailer: backorder_share}
    print(f"Backorder share of {retailer} ({PLACES_M4[retailer][0]}): {_number(backorder_share, 2)}; "
          f"lost sales, the rest: {_number(1 - backorder_share, 2)}.")
    return _report({"backorder_share": share}, FORECAST, full=False)


def lost_sale_cost_test(lost_sale_cost: float = 700) -> dict | None:
    """The plan with forecast 5 and the lost-sale cost, the price that the retailers
    pay for a bike, changed for every retailer."""
    print(f"Lost-sale cost: {_number(lost_sale_cost)} €/bike.")
    return _report({"lost_sale_cost": {r: lost_sale_cost for r in RETAILERS}}, FORECAST, full=False)


def promotion_test(retailer: str = "Retailer 2", month: str = "Jan", extra_orders: float = 100) -> dict | None:
    """The plan with forecast 5 and more orders of one retailer in one month."""
    if retailer not in RETAILERS:
        raise ValueError(f"The retailer must be one of {', '.join(RETAILERS)}.")
    order = orders()
    order[retailer, month] += extra_orders
    print(f"Orders of {retailer} ({PLACES_M4[retailer][0]}) in {month}: {_number(order[retailer, month])} bikes, "
          f"{_number(extra_orders)} more than in {FORECAST.lower()}.")
    return _report({"order": order}, FORECAST, month, full=False)


def transport_cost_test(arc: int = 17, transport_cost: float = 1.05) -> dict | None:
    """The plan with forecast 5 and the transport cost of one arc from a local
    warehouse to a retailer changed (arcs 14 to 25)."""
    if not FIRST_RETAILER_ARC < arc <= len(ARCS_M4):
        raise ValueError(f"The arc must be one of {FIRST_RETAILER_ARC + 1} to {len(ARCS_M4)}.")
    arc_list = [dict(a) for a in ARCS_M4]
    arc_list[arc - 1]["cost"] = transport_cost
    print(f"Transport cost of arc {arc}, {arc_name(arc_list[arc - 1])}: {_number(transport_cost, 2)} €/bike.")
    solution = solve(arc_list=arc_list)
    if solution is not None:
        _display(pd.DataFrame({t: {f"{a + 1}. {arc_name(arc_list[a])}": solution["flow"][a, t]
                                   for a in range(FIRST_RETAILER_ARC, len(arc_list))} for t in solution["months"]})
                 .rename_axis("Flow from the local warehouses to the retailers (bikes)"))
    return _report({"arc_list": arc_list}, FORECAST, full=False)
