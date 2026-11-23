"""M4 · Retailers (retailers.md): the network of distribution_network.md (M3) with
the retailers as a new stage at its end. The retailers receive the orders; of the
demand that a retailer does not receive in its month, the backorder share is
backordered and the rest is lost sales. Written with PuLP and solved with HiGHS;
and what the notebook retailers.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the retailers, their arcs, their orders and backorder shares;
2. ``retailer_plan``: the plan with forecast 5, with the flows of each month;
3. ``backorder_share_test``, ``lost_sale_cost_test``, ``promotion_test`` and
   ``transport_cost_test``: the plan when one datum changes.

Each one shows interactive figures, drawn with Plotly (``interactive``), or, with
``show_tables``, the same data in tables.

The model reuses the list of arcs and the functions ``entering`` and ``leaving``
of M3, and the check of a single optimal plan of M2; M3 does not change.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .central_warehouse import SEVERAL, only_optimal
from .data import (ARCS_M4, BACKORDER_SHARE, CENTRAL, FORECAST_5, FORECAST_5_NAME, F, K, K_h_node, K_h_node_m4, K_n,
                   LOCAL, NODES, NODES_M4, PLACES_M4, RAIL_TERMINAL, RETAILERS, REGIONAL, SHARE_M4, T, b_0, c, c_b,
                   c_h_node_m4, c_l, h_node_0_m4, h_node_end_m4)
from .distribution_network import (PRICES, _assembly_figure, _kind, _prices_figure, _stock_figure, arc_name,
                                   entering, leaving, places_table)
from .model import TOL, _constraints, _optimal
from . import figures, interactive
from .show import _display, _number, _say

FORECAST = FORECAST_5_NAME               # M4 is solved with forecast 5
DEMAND = FORECAST_5
FIRST_RETAILER_ARC = len(ARCS_M4) - 12    # arcs 14 to 25 of the list go to the retailers
# The colour of each retailer in the figures with one series per retailer: the
# soft palette Set2, as the local warehouses that receive the orders in M3, so that
# no retailer takes the colour of a plant or of a stage of the network
RETAILER_COLOURS = dict(zip(RETAILERS, [plt.get_cmap("Set2")(k) for k in range(6)]))
ARC_PAIR = (figures.INK, "#8FB9C0")       # the two arcs to a retailer: dark and light teal, as the arcs of the network

def _key(node: str) -> str:
    return node.replace(" ", "")


def orders(demand: dict = DEMAND, share: dict = SHARE_M4, months=T) -> dict:
    """The orders of each retailer in each month (bikes): its share of the forecast."""
    return {(r, t): share[r] * demand[t] for r in share for t in months}


def build(order: dict | None = None, months=T, arc_list: list = ARCS_M4, backorder_share: dict = BACKORDER_SHARE,
          lost_sale_cost: dict = c_l, holding: dict = c_h_node_m4, storage: dict = K_h_node_m4,
          node_capacity: dict = K_n, initial: dict = h_node_0_m4, final: dict | None = h_node_end_m4,
          backorder_cost: float = c_b, backorders_initial: float = b_0, capacity: dict = K, nodes=NODES_M4,
          plants=F, retailers=RETAILERS, extra_storage: dict | None = None):
    """The model of M4, not solved. ``order`` gives the orders of each retailer in
    each month, by (r, t); by default, its share of forecast 5. ``extra_storage``
    adds bikes to the storage capacity of a node in one month only, by (i, t).
    Returns the model, a dict of its variables by kind ("p" by (f, t); "x" by
    (a, t); "h" by (i, t); "s", "b", "l" by (r, t)) and the cost expression."""
    order = order or orders(months=months)
    extra_storage = extra_storage or {}
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
            model += (h[i, t] <= storage[i] + extra_storage.get((i, t), 0), f"storage_{_key(i)}_{t}")
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


def storage_price_breakdown(node: str = "Local warehouse 4", month: str = "Mar", extra: float = 1,
                            **data) -> list[dict]:
    """The change in each term of the cost when the storage capacity of a node rises
    by ``extra`` bikes in one month only (Table 10 of retailers.md): the plan with
    that capacity less the plan with the data given (the other arguments of
    ``build``). One row per variable that changes: its term of the cost, where and
    when, its change (bikes), its unit cost and the change in cost (EUR). While the
    same capacities are full, the rows add up to ``extra`` times the shadow price of
    that storage capacity."""
    base = solve(**data)
    new = solve(**data, extra_storage={(node, month): extra})
    arc_list = data.get("arc_list", ARCS_M4)
    holding = data.get("holding", c_h_node_m4)
    lost_sale_cost = data.get("lost_sale_cost", c_l)
    unit = {"assembly": lambda key: c[key[0]], "stock": lambda key: holding[key[0]],
            "flow": lambda key: arc_list[key[0]]["cost"], "backorders": lambda key: data.get("backorder_cost", c_b),
            "lost sales": lambda key: lost_sale_cost[key[0]]}
    terms = {"assembly": "Assembly", "stock": "Holding", "flow": "Transport", "backorders": "Backorders",
             "lost sales": "Lost sales"}
    rows = []
    for kind, term in terms.items():
        for key, value in base[kind].items():
            change = new[kind][key] - value
            if abs(change) > TOL:
                where = (f"{key[0] + 1}. {arc_name(arc_list[key[0]])}" if kind == "flow"
                         else _name(key[0]) if key[0] in RETAILERS else key[0])
                rows.append({"term": term, "where": where, "month": key[1], "change": change,
                             "unit cost": unit[kind](key), "cost": change * unit[kind](key)})
    return rows


def m3_has_no_solution(demand: dict = DEMAND) -> bool:
    """True if M3, with the demand at the local warehouses split as in M3, has no
    solution for a demand."""
    from . import distribution_network
    return distribution_network.solve(demand=demand) is None


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def _name(node: str) -> str:
    """A node with its place: «Retailer 1 (Lleida)»."""
    return f"{node} ({PLACES_M4[node][0]})"


def show_data(show_tables: bool = False) -> None:
    """The places of the network on the map, the network with the data of each node
    and arc, and the orders of each retailer; with ``show_tables``, the places of
    the network and Tables 1 to 3 of retailers.md instead of the figures."""
    _say(f"{FORECAST} (bikes/month): " + "; ".join(f"{t} {_number(DEMAND[t])}" for t in T) + ".")
    order = orders()
    if not show_tables:
        interactive.show(interactive.places_map([(_kind(i), i, *PLACES_M4[i]) for i in NODES_M4],
                                                "Places of the nodes of the network of M4"))
        interactive.show(data_network())
        capacity = sum(K[f]["Jan"] for f in F)
        rows = {f"{_name(r)}, {_number(100 * SHARE_M4[r])} %": [order[r, t] for t in T] for r in RETAILERS}
        interactive.show(interactive.bars(
            T, rows, {row: interactive.colour(RETAILER_COLOURS[r]) for row, r in zip(rows, RETAILERS)},
            f"{FORECAST}: orders of each retailer (bikes/month)", ytitle="bikes/month",
            line=capacity, line_label=f"assembly capacity of the three plants, {_number(capacity)}"))
        return
    _display(places_table(NODES_M4, PLACES_M4))
    _display(pd.DataFrame([{"Arc": a + 1, "Origin": arc["origin"], "Destination": arc["destination"],
                            "Distance (km)": _number(arc["km"], 1), "Transport cost (€/bike)": _number(arc["cost"], 2),
                            "Arc capacity (bikes/month)": _number(arc["capacity"])}
                           for a, arc in enumerate(ARCS_M4) if a >= FIRST_RETAILER_ARC]).set_index("Arc"))
    table = pd.DataFrame({r: {t: order[r, t] for t in T} for r in RETAILERS}).T
    table.insert(0, "Share", [f"{_number(100 * SHARE_M4[r])} %" for r in RETAILERS])
    table.insert(1, "Backorder share", [_number(BACKORDER_SHARE[r], 1) for r in RETAILERS])
    table.insert(2, "Lost-sale cost (€/bike)", [c_l[r] for r in RETAILERS])
    _display(table.rename_axis("Orders (bikes/month)"))


def _retailer_table(solution: dict) -> pd.DataFrame:
    months = solution["months"]
    rows = {}
    for label, key in (("Orders", "orders"), ("Deliveries", "deliveries"),
                       ("Backorders at the end of the month", "backorders"), ("Lost sales", "lost sales")):
        for r in RETAILERS:
            rows[label, _name(r)] = {t: solution[key][r, t] for t in months}
    return pd.DataFrame(rows).T.rename_axis(["Bikes", "Retailer"])


def _assembly_table(solution: dict) -> pd.DataFrame:
    return (pd.DataFrame({t: {f: solution["assembly"][f, t] for f in F} for t in solution["months"]})
            .rename_axis("Assembly (bikes)"))


def _tables(solution: dict) -> None:
    months, arc_list = solution["months"], solution["arcs"]
    _display(_assembly_table(solution))
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
        _say(PRICES)
        _display(pd.DataFrame(rows).T.rename_axis("Capacity"))


def _lost_sales_table(solution: dict) -> pd.DataFrame:
    return (pd.DataFrame({t: {_name(r): solution["lost sales"][r, t] for r in RETAILERS} for t in solution["months"]})
            .rename_axis("Lost sales (bikes)"))


# ---------------------------------------------------------------------------
# Interactive figures (Plotly)
# ---------------------------------------------------------------------------

XMAX = 1680          # right end of the network: room for the retailers and their names


def _node_name(i: str) -> str:
    return f"<b>{i}</b> ({PLACES_M4[i][0]})"


def _arc_label(a: int, arc: dict) -> str:
    return f"<b>arc {a + 1}</b>: {arc_name(arc)} ({arc['mode'].lower()})"


def data_network():
    """The network with the data of M4: the data of each node and arc in its label,
    and a dropdown of what is written on the arcs."""
    nodes = {}
    for i in NODES_M4:
        if i == RAIL_TERMINAL:
            nodes[i] = f"{_node_name(i)}<br>holds no stock"
            continue
        if i in RETAILERS:
            nodes[i] = "<br>".join([_node_name(i), f"backorder share {_number(BACKORDER_SHARE[i], 1)}",
                                    f"lost-sale cost {_number(c_l[i])} €/bike", "holds no stock"])
            continue
        lines = [f"unit assembly cost {_number(c[i])} €/bike", f"capacity {_number(K[i]['Jan'])} bikes/month"] \
            if i in F else []
        lines += [f"holding cost {_number(c_h_node_m4[i])} €/(bike·month)",
                  f"storage capacity {_number(K_h_node_m4[i])} bikes", f"initial stock {_number(h_node_0_m4[i])} bikes",
                  f"required final stock {_number(h_node_end_m4[i])} bikes"]
        if i in K_n:
            lines.append(f"node capacity {_number(K_n[i])} bikes/month")
        nodes[i] = "<br>".join([_node_name(i), *lines])
    arcs = {a: f"{_arc_label(a, arc)}<br>distance {_number(arc['km'], 1)} km<br>"
               f"transport cost {_number(arc['cost'], 2)} €/bike<br>arc capacity {_number(arc['capacity'])} bikes/month"
            for a, arc in enumerate(ARCS_M4)}
    text = {"Transport cost (€/bike)": lambda a, arc: _number(arc["cost"], 2),
            "Arc capacity (bikes/month)": lambda a, arc: _number(arc["capacity"]),
            "Arc number": lambda a, arc: str(a + 1)}
    options = {label: dict(title=f"Data of M4. On each arc: {label[0].lower() + label[1:]}",
                           text_last=range(FIRST_RETAILER_ARC, len(ARCS_M4)),
                           arc_text={a: write(a, arc) for a, arc in enumerate(ARCS_M4)}, arc_hover=arcs,
                           node_hover=nodes)
               for label, write in text.items()}
    return interactive.network(NODES_M4, ARCS_M4, options, xmax=XMAX)


def _node_month(solution: dict, i: str, t: str, node_capacity: dict = K_n) -> str:
    """The label of a node in the network of one month: for a retailer, its orders,
    deliveries and lost sales in the month and its backorders at the end of it; for
    any other node, as in M3, with its stock at the end of the month."""
    if i == RAIL_TERMINAL:
        return f"{_node_name(i)}<br>holds no stock"
    lines = [_node_name(i)]
    if i in RETAILERS:
        lines += [f"orders in {t}: {_number(solution['orders'][i, t])} bikes",
                  f"deliveries in {t}: {_number(solution['deliveries'][i, t])} bikes",
                  f"lost sales in {t}: {_number(solution['lost sales'][i, t])} bikes",
                  f"backorders at the end of {t}: {_number(solution['backorders'][i, t])} bikes",
                  f"backorder share {_number(BACKORDER_SHARE[i], 1)}"]
        return "<br>".join(lines)
    if i in F:
        lines.append(f"assembled in {t}: {_number(solution['assembly'][i, t])} bikes")
    if i in node_capacity:
        lines.append(f"received in {t}: {_number(figures._arriving(solution, i, t))} bikes "
                     f"(node capacity {_number(node_capacity[i])})")
    lines.append(f"stock at the end of {t}: {_number(solution['stock'][i, t])} bikes")
    return "<br>".join(lines)


def _flow_network(solution: dict, node_capacity: dict = K_n, first: str = "May"):
    """The network with the flow on each arc, one month at a time, with a dropdown
    of the months that opens in ``first``: an arc whose capacity is full in red, an
    arc with no flow in light grey; the data of each node and arc in the month in
    its label."""
    arc_list, options = solution["arcs"], {}
    for t in solution["months"]:
        full = figures.full_arcs(solution, t)
        flow = {a: solution["flow"][a, t] for a in range(len(arc_list))}
        options[t] = dict(
            title=f"Plan of M4 in {t}: flow on each arc (bikes)", full=full,
            text_last=range(FIRST_RETAILER_ARC, len(arc_list)),
            idle=[a for a, v in flow.items() if v <= TOL], arc_text={a: _number(v) for a, v in flow.items()},
            arc_hover={a: f"{_arc_label(a, arc)}<br>flow in {t}: {_number(flow[a])} bikes<br>arc capacity "
                          f"{_number(arc['capacity'])} bikes/month" + (", full" if a in full else "")
                       for a, arc in enumerate(arc_list)},
            node_hover={i: _node_month(solution, i, t, node_capacity) for i in NODES_M4})
    return interactive.network(NODES_M4, arc_list, options, first=first, xmax=XMAX)


def _lost_sales_figure(solution: dict):
    """The lost sales of each retailer in each month, stacked, each retailer in its
    colour."""
    rows = {_name(r): [solution["lost sales"][r, t] for t in solution["months"]] for r in RETAILERS}
    return interactive.bars(solution["months"], rows,
                            {_name(r): interactive.colour(RETAILER_COLOURS[r]) for r in RETAILERS},
                            "Lost sales of each retailer in each month (bikes)", top=max(
                                1.25 * max(sum(v[k] for v in rows.values()) for k in range(len(solution["months"]))),
                                10))


def _arc_pair_figure(solution: dict, arc: int):
    """The flow in each month on the two arcs that reach the retailer of an arc,
    side by side, with the transport cost of each arc in the legend."""
    import plotly.graph_objects as go

    arc_list, months = solution["arcs"], solution["months"]
    retailer = arc_list[arc]["destination"]
    fig = go.Figure()
    for k, a in enumerate(entering(retailer, arc_list)):
        label = (f"arc {a + 1}, from {_name(arc_list[a]['origin'])}: "
                 f"{_number(arc_list[a]['cost'], 2)} €/bike")
        flows = [solution["flow"][a, t] for t in months]
        # a month in which the arc capacity is full in red, as in the network
        full = [v > TOL and abs(v - arc_list[a]["capacity"]) < TOL for v in flows]
        fig.add_bar(x=months, y=flows, name=label, marker_color=[interactive.FULL if f else ARC_PAIR[k] for f in full],
                    text=[_number(v) for v in flows], textposition="outside",
                    customdata=[", arc capacity full" if f else "" for f in full],
                    hovertemplate=f"{label}<br>%{{x}}: %{{y:,.0f}} bikes%{{customdata}}<extra></extra>")
    top = max(max(solution["flow"][a, t] for a in entering(retailer, arc_list) for t in months), 1)
    fig.update_layout(**interactive.LAYOUT, barmode="group", height=interactive.MONTH_HEIGHT,
                      title=dict(text=f"Flow on the two arcs to {_name(retailer)} (bikes)", font_size=14),
                      yaxis=dict(title="bikes", range=[0, 1.15 * top]))
    interactive._legend_below(fig)
    return fig


def _report(data: dict, heading: str, full: bool = True, show_tables: bool = False, arc: int | None = None,
            first: str = "May") -> dict | None:
    """Solve M4 with the data given and show its cost, its lost sales and whether
    other plans have the same cost; then the plan in figures or, with
    ``show_tables``, in tables. With ``full``, the network of each month, the
    assembly, the stock at each stage, the lost sales and the shadow prices of the
    full capacities; without it, the lost sales, the assembly and the network of
    each month. The network opens in the month ``first``. With ``arc``, first the
    flow on the two arcs to the retailer of that arc (a position in the list)."""
    solution = solve(**data)
    if solution is None:
        _say(f"{heading}: the model has no solution.")
        return None
    lost = sum(solution["lost sales"].values())
    _say(f"{heading}: optimal plan, cost {_number(solution['cost'], 2)} €; lost sales {_number(lost)} bikes.")
    if not only_plan(**data):
        _say(SEVERAL)
    if show_tables:
        if arc is not None:
            arc_list = solution["arcs"]
            _display(pd.DataFrame({t: {f"{a + 1}. {arc_name(arc_list[a])}": solution["flow"][a, t]
                                       for a in range(FIRST_RETAILER_ARC, len(arc_list))} for t in solution["months"]})
                     .rename_axis("Flow from the local warehouses to the retailers (bikes)"))
        if full:
            _tables(solution)
            _prices(solution)
        else:
            _display(_lost_sales_table(solution))
            _display(_assembly_table(solution))
        return solution
    node_capacity = data.get("node_capacity", K_n)
    if arc is not None:
        interactive.show(_arc_pair_figure(solution, arc))
    if full:
        interactive.show(_flow_network(solution, node_capacity, first))
        interactive.show(_assembly_figure(solution, data.get("capacity", K)))
        interactive.show(_stock_figure(solution))
        interactive.show(_lost_sales_figure(solution))
        interactive.show(_prices_figure(solution, node_capacity))
    else:
        interactive.show(_lost_sales_figure(solution))
        interactive.show(_assembly_figure(solution, data.get("capacity", K)))
        interactive.show(_flow_network(solution, node_capacity, first))
    return solution


def retailer_plan(show_tables: bool = False) -> dict | None:
    """The plan with forecast 5, with the flows of each month on the network; and,
    first, whether M3 has a plan for forecast 5."""
    if m3_has_no_solution():
        ordered = sum(DEMAND[t] for t in T[3:])
        assembled = sum(K[f][t] for f in F for t in T[3:])
        ending = sum(h_node_end_m4[f] for f in F)
        _say(f"M3, with the orders at the local warehouses, has no solution with the {FORECAST.lower()}: from April "
              f"to June {_number(ordered)} bikes are ordered and the plants can assemble {_number(assembled)}, "
              f"and the plants have to end June with {_number(ending)} bikes. At the end of March "
              f"{_number(ordered - assembled + ending)} bikes have to be in stock, and the network can hold "
              f"{_number(sum(K_h_node[i] for i in NODES))}.")
        _say()
    return _report({}, FORECAST, show_tables=show_tables)


def backorder_share_test(retailer: str = "Retailer 6", backorder_share: float = 0.4,
                         show_tables: bool = False) -> dict | None:
    """The plan with forecast 5 and the backorder share of one retailer changed."""
    if retailer not in RETAILERS:
        raise ValueError(f"The retailer must be one of {', '.join(RETAILERS)}.")
    share = {**BACKORDER_SHARE, retailer: backorder_share}
    _say(f"Backorder share of {_name(retailer)}: {_number(backorder_share, 2)}; "
          f"lost sales, the rest: {_number(1 - backorder_share, 2)}.")
    return _report({"backorder_share": share}, FORECAST, full=False, show_tables=show_tables)


def lost_sale_cost_test(lost_sale_cost: float = 700, show_tables: bool = False) -> dict | None:
    """The plan with forecast 5 and the lost-sale cost, the price that the retailers
    pay for a bike, changed for every retailer."""
    _say(f"Lost-sale cost: {_number(lost_sale_cost)} €/bike.")
    return _report({"lost_sale_cost": {r: lost_sale_cost for r in RETAILERS}}, FORECAST, full=False,
                   show_tables=show_tables)


def promotion_test(retailer: str = "Retailer 2", month: str = "Jan", extra_orders: float = 100,
                   show_tables: bool = False) -> dict | None:
    """The plan with forecast 5 and more orders of one retailer in one month; the
    network opens in that month."""
    if retailer not in RETAILERS:
        raise ValueError(f"The retailer must be one of {', '.join(RETAILERS)}.")
    if month not in T:
        raise ValueError(f"The month must be one of {', '.join(T)}.")
    order = orders()
    order[retailer, month] += extra_orders
    _say(f"Orders of {_name(retailer)} in {month}: {_number(order[retailer, month])} bikes, "
          f"{_number(extra_orders)} more than in the {FORECAST.lower()}.")
    return _report({"order": order}, FORECAST, full=False, show_tables=show_tables, first=month)


def transport_cost_test(arc: int = 17, transport_cost: float = 1.05, show_tables: bool = False) -> dict | None:
    """The plan with forecast 5 and the transport cost of one arc from a local
    warehouse to a retailer changed (arcs 14 to 25)."""
    if not FIRST_RETAILER_ARC < arc <= len(ARCS_M4):
        raise ValueError(f"The arc must be one of {FIRST_RETAILER_ARC + 1} to {len(ARCS_M4)}.")
    arc_list = [dict(a) for a in ARCS_M4]
    arc_list[arc - 1]["cost"] = transport_cost
    _say(f"Transport cost of arc {arc}, {arc_name(arc_list[arc - 1])}: {_number(transport_cost, 2)} €/bike.")
    return _report({"arc_list": arc_list}, FORECAST, full=False, show_tables=show_tables, arc=arc - 1)
