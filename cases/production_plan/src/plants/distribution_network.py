"""M3 · Distribution network (distribution_network.md): the model of
central_warehouse.md (M2) written on a network given as a list of arcs, with
regional and local warehouses, a rail terminal, transport costs, arc capacities
and node capacities, written with PuLP and solved with HiGHS; and what the
notebook distribution_network.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the nodes, the list of arcs and forecast 4;
2. ``network_plan``: the plan with forecast 4, with the flows of each month;
3. ``node_capacity_test``: the plan when one datum changes;
4. ``month_flows``: an analysis of the plan, not a version of the model: the
   minimum cost flow problem of each month.

Each one shows interactive figures, drawn with Plotly (``interactive``), or, with
``show_tables``, the same data in tables.

The arcs are dicts with origin, destination, mode, distance (km), capacity
(bikes/month) and transport cost (EUR/bike), as in ``data.arcs``; an arc is
referred to by its position in the list. Node data are dicts by node.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .central_warehouse import SEVERAL, only_optimal
from .data import (ARCS, CENTRAL, F, FORECAST_4, FORECAST_4_NAME, K, K_h_node, K_n, LOCAL, NODES, PLACES, RAIL,
                   RAIL_TERMINAL, REGIONAL, SHARE, TRANSPORT_RATE, T, b_0, b_max, c, c_b, c_h_node,
                   h_node_0, h_node_end)
from .model import TOL, _constraints, _optimal
from . import figures, interactive
from .show import COLOURS, _display, _number, _say

FORECAST = FORECAST_4_NAME               # M3 is solved with forecast 4
DEMAND = FORECAST_4
RAIL_ARC = next(a for a, arc in enumerate(ARCS) if arc["mode"] == RAIL)

def _key(node: str) -> str:
    return node.replace(" ", "")


def arc_name(arc: dict) -> str:
    return f"{arc['origin']} → {arc['destination']}"


def entering(node: str, arc_list: list) -> list[int]:
    """The arcs that enter a node (positions in the list)."""
    return [a for a, arc in enumerate(arc_list) if arc["destination"] == node]


def leaving(node: str, arc_list: list) -> list[int]:
    """The arcs that leave a node (positions in the list)."""
    return [a for a, arc in enumerate(arc_list) if arc["origin"] == node]


def build(demand: dict = DEMAND, months=T, arc_list: list = ARCS, share: dict = SHARE, holding: dict = c_h_node,
          storage: dict = K_h_node, node_capacity: dict = K_n, initial: dict = h_node_0,
          final: dict | None = h_node_end, backorder_cost: float = c_b, backorders_initial: float = b_0,
          backorders_end: float | None = b_max, capacity: dict = K, nodes=NODES, plants=F):
    """The model of M3, not solved. ``share`` gives the demand nodes and the share
    of the demand that each one receives. Returns the model, a dict of its variables
    by kind ("p" by (f, t); "x" by (a, t); "h" by (i, t); "s", "b" by (i, t) at the
    demand nodes) and the cost expression."""
    model = pulp.LpProblem("distribution_network", pulp.LpMinimize)
    demand_nodes = list(share)
    # p[f, t] = bikes assembled at plant f; x[a, t] = bikes shipped on arc a;
    # s[i, t] = deliveries of node i (bikes/month); h[i, t] = stock of node i at the
    # end of month t; b[i, t] = backorders of node i at the end of month t (bikes)
    p = {(f, t): model.add_variable(f"p_{_key(f)}_{t}", lowBound=0) for f in plants for t in months}
    x = {(a, t): model.add_variable(f"x_{a}_{t}", lowBound=0) for a in range(len(arc_list)) for t in months}
    h = {(i, t): model.add_variable(f"h_{_key(i)}_{t}", lowBound=0) for i in nodes for t in months}
    s = {(i, t): model.add_variable(f"s_{_key(i)}_{t}", lowBound=0) for i in demand_nodes for t in months}
    b = {(i, t): model.add_variable(f"b_{_key(i)}_{t}", lowBound=0) for i in demand_nodes for t in months}
    # Minimise the assembly, holding, transport and backorder cost
    cost = (pulp.lpSum(c[f] * p[f, t] for f in plants for t in months)
            + pulp.lpSum(holding[i] * h[i, t] for i in nodes for t in months)
            + pulp.lpSum(arc_list[a]["cost"] * x[a, t] for a in range(len(arc_list)) for t in months)
            + pulp.lpSum(backorder_cost * b[i, t] for i in demand_nodes for t in months))
    model += cost
    for i in nodes:
        into, out = entering(i, arc_list), leaving(i, arc_list)
        for k, t in enumerate(months):
            before = initial[i] if k == 0 else h[i, months[k - 1]]
            assembled = p[i, t] if i in plants else 0
            delivered = s[i, t] if i in demand_nodes else 0
            arriving = pulp.lpSum(x[a, t] for a in into)
            shipped = pulp.lpSum(x[a, t] for a in out)
            # Stock balance: stock at the start of the month, plus what the node
            # assembles and what arrives, equals what leaves on its arcs, plus its
            # deliveries, plus its stock at the end of the month
            model += (before + assembled + arriving == shipped + delivered + h[i, t], f"balance_{_key(i)}_{t}")
            # Shipment limit: what leaves is at most the stock of the previous month,
            # plus what the node assembles and what arrives that month
            model += (shipped + delivered <= before + assembled + arriving, f"shipment_limit_{_key(i)}_{t}")
            model += (h[i, t] <= storage[i], f"storage_{_key(i)}_{t}")
            if i in node_capacity:
                model += (arriving <= node_capacity[i], f"node_capacity_{_key(i)}_{t}")
        if final is not None:
            model += (h[i, months[-1]] >= final[i], f"final_stock_{_key(i)}")
    for i in demand_nodes:
        for k, t in enumerate(months):
            before = backorders_initial if k == 0 else b[i, months[k - 1]]
            # Backorder balance, written with the orders on the right, so that its
            # shadow price is what one more order costs
            model += (s[i, t] + b[i, t] - before == share[i] * demand[t], f"backorders_{_key(i)}_{t}")
        if backorders_end is not None:
            model += (b[i, months[-1]] <= backorders_end, f"backorders_at_the_end_{_key(i)}")
    for a in range(len(arc_list)):
        for t in months:
            model += (x[a, t] <= arc_list[a]["capacity"], f"arc_capacity_{a}_{t}")
    for f in plants:
        for t in months:
            model += (p[f, t] <= capacity[f][t], f"capacity_{_key(f)}_{t}")
    return model, {"p": p, "x": x, "h": h, "s": s, "b": b}, cost


def only_plan(**data) -> bool | None:
    """True if the optimal plan of M3 with the data given (the arguments of ``build``)
    is the only one; False if several plans have the optimal cost; None if the
    model has no solution."""
    model, var, cost = build(**data)
    return only_optimal(model, [v for kind in var.values() for v in kind.values()], cost)


def solve(**data) -> dict | None:
    """Solve M3 with the data given (the arguments of ``build``). Returns the cost
    (EUR); the bikes assembled at each plant, shipped on each arc, in stock at each
    node, and the deliveries and backorders of each demand node, by month
    (bikes); and the shadow prices of the arc, node and storage capacities
    (EUR/bike). None if the model has no solution."""
    model, var, _ = build(**data)
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    months = sorted({t for _, t in var["p"]}, key=T.index)
    arc_list = data.get("arc_list", ARCS)
    nodes = data.get("nodes", NODES)
    node_capacity = data.get("node_capacity", K_n)
    cons = _constraints(model)
    clean = lambda v: 0.0 if abs(v) < TOL else v      # noqa: E731  (no "-0.0" in tables)
    values = {kind: {key: clean(v.value()) for key, v in var[kind].items()} for kind in var}
    return {
        "months": months, "arcs": arc_list,
        "cost": pulp.value(model.objective),
        "assembly": values["p"], "flow": values["x"], "stock": values["h"],
        "deliveries": values["s"], "backorders": values["b"],
        "orders price": {(i, t): clean(cons[f"backorders_{_key(i)}_{t}"].pi)
                         for i in data.get("share", SHARE) for t in months},
        "arc price": {(a, t): clean(cons[f"arc_capacity_{a}_{t}"].pi) for a in range(len(arc_list)) for t in months},
        "node price": {(i, t): clean(cons[f"node_capacity_{_key(i)}_{t}"].pi) for i in node_capacity for t in months},
        "storage price": {(i, t): clean(cons[f"storage_{_key(i)}_{t}"].pi) for i in nodes for t in months},
    }


def m2_has_no_solution(demand: dict = DEMAND) -> bool:
    """True if M2, with the plants and the central warehouse only, has no solution
    for a demand."""
    from . import central_warehouse
    return central_warehouse.solve(demand=demand) is None


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def _kind(node: str) -> str:
    """The kind of a node on the map: its name without its number."""
    return node.rstrip("0123456789 ")


def places_table(nodes: list, places: dict) -> pd.DataFrame:
    """The place of each node, with its latitude and longitude: the data of the map."""
    return pd.DataFrame({i: {"Place": places[i][0], "Latitude": _number(places[i][1], 4),
                             "Longitude": _number(places[i][2], 4)} for i in nodes}).T.rename_axis("Node")


def show_data(show_tables: bool = False) -> None:
    """The places of the nodes on the map, the network with the data of each node
    and arc, and the orders of each local warehouse; with ``show_tables``, Tables 1
    to 4 of distribution_network.md instead of the figures."""
    _say(f"Transport rate (€/(bike·km)): road {_number(TRANSPORT_RATE['Road'], 3)}; "
          f"rail {_number(TRANSPORT_RATE['Rail'], 3)}.")
    orders = {i: [SHARE[i] * DEMAND[t] for t in T] for i in LOCAL}
    if not show_tables:
        interactive.show(interactive.places_map([(_kind(i), i, *PLACES[i]) for i in NODES],
                                                "Places of the nodes of the network of M3"))
        interactive.show(data_network())
        capacity = sum(K[f]["Jan"] for f in F)
        rows = {f"{i} ({PLACES[i][0]}), {_number(100 * SHARE[i])} %": orders[i] for i in LOCAL}
        set2 = plt.get_cmap("Set2")
        interactive.show(interactive.bars(
            T, rows, {row: interactive.colour(set2(k)) for k, row in enumerate(rows)},
            f"{FORECAST}: orders of each local warehouse (bikes/month)", ytitle="bikes/month",
            line=capacity, line_label=f"assembly capacity of the three plants, {_number(capacity)}"))
        return
    _display(places_table(NODES, PLACES))
    _display(pd.DataFrame([{"Arc": a + 1, "Origin": arc["origin"], "Destination": arc["destination"],
                            "Mode": arc["mode"], "Distance (km)": _number(arc["km"], 1),
                            "Transport cost (€/bike)": _number(arc["cost"], 2),
                            "Arc capacity (bikes/month)": _number(arc["capacity"])}
                           for a, arc in enumerate(ARCS)]).set_index("Arc"))
    _display(pd.DataFrame({i: {"Holding cost (€/(bike·month))": c_h_node[i], "Storage capacity (bikes)": K_h_node[i],
                               "Initial stock (bikes)": h_node_0[i],
                               "Required final stock (bikes)": h_node_end[i],
                               "Node capacity (bikes/month)": K_n.get(i, "—")} for i in NODES}).T.rename_axis("Node"))
    table = pd.DataFrame({**{i: dict(zip(T, orders[i])) for i in LOCAL}, FORECAST: DEMAND}).T
    table.insert(0, "Share", [f"{_number(100 * SHARE[i])} %" for i in LOCAL] + ["100 %"])
    _display(table.rename_axis("Orders (bikes/month)"))


def _node_name(i: str) -> str:
    return f"<b>{i}</b> ({PLACES[i][0]})"


def _arc_label(a: int, arc: dict) -> str:
    return f"<b>arc {a + 1}</b>: {arc_name(arc)} ({arc['mode'].lower()})"


def data_network():
    """The network with the data of M3: the data of each node and arc in its label,
    and a dropdown of what is written on the arcs."""
    nodes = {}
    for i in NODES:
        if i == RAIL_TERMINAL:
            nodes[i] = f"{_node_name(i)}<br>holds no stock"
            continue
        lines = [f"unit assembly cost {_number(c[i])} €/bike", f"capacity {_number(K[i]['Jan'])} bikes/month"] \
            if i in F else []
        lines += [f"holding cost {_number(c_h_node[i])} €/(bike·month)", f"storage capacity {_number(K_h_node[i])} bikes",
                  f"initial stock {_number(h_node_0[i])} bikes", f"required final stock {_number(h_node_end[i])} bikes"]
        if i in K_n:
            lines.append(f"node capacity {_number(K_n[i])} bikes/month")
        nodes[i] = "<br>".join([_node_name(i), *lines])
    arcs = {a: f"{_arc_label(a, arc)}<br>distance {_number(arc['km'], 1)} km<br>"
               f"transport cost {_number(arc['cost'], 2)} €/bike<br>arc capacity {_number(arc['capacity'])} bikes/month"
            for a, arc in enumerate(ARCS)}
    text = {"Transport cost (€/bike)": lambda a, arc: _number(arc["cost"], 2),
            "Arc capacity (bikes/month)": lambda a, arc: _number(arc["capacity"]),
            "Arc number": lambda a, arc: str(a + 1)}
    options = {label: dict(title=f"Data of M3. On each arc: {label[0].lower() + label[1:]}",
                           arc_text={a: write(a, arc) for a, arc in enumerate(ARCS)}, arc_hover=arcs, node_hover=nodes)
               for label, write in text.items()}
    return interactive.network(NODES, ARCS, options)


def _flow_table(solution: dict) -> pd.DataFrame:
    arc_list, months = solution["arcs"], solution["months"]
    return pd.DataFrame({t: {f"{a + 1}. {arc_name(arc)}": solution["flow"][a, t] for a, arc in enumerate(arc_list)}
                         for t in months}).rename_axis("Flow on each arc (bikes)")


def _tables(solution: dict) -> None:
    months = solution["months"]
    _display(pd.DataFrame({t: {f: solution["assembly"][f, t] for f in F} for t in months})
             .rename_axis("Assembly (bikes)"))
    _display(_flow_table(solution))
    _display(pd.DataFrame({t: {i: solution["stock"][i, t] for i in NODES} for t in months})
             .rename_axis("Stock at the end of the month (bikes)"))
    rows = {}
    for i in SHARE:
        rows["Deliveries", i] = {t: solution["deliveries"][i, t] for t in months}
    for i in SHARE:
        rows["Backorders at the end of the month", i] = {t: solution["backorders"][i, t] for t in months}
    _display(pd.DataFrame(rows).T.rename_axis(["Bikes", "Local warehouse"]))


PRICES = ("Shadow price of each capacity that is full in some month (€/bike). A capacity is full when the plan uses "
          "all of it in the month; its shadow price is the change in the cost of the plan with one more bike of that "
          "capacity in that month (negative: a saving).")


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
    # A storage capacity that is full in some month, also with a shadow price of 0
    for i in NODES:
        if i != RAIL_TERMINAL and any(solution["storage price"][i, t] or abs(solution["stock"][i, t] - K_h_node[i]) < TOL
                                      for t in months):
            rows[f"Storage capacity, {i}"] = {t: solution["storage price"][i, t] for t in months}
    if rows:
        _say(PRICES)
        _display(pd.DataFrame(rows).T.rename_axis("Capacity"))


def stage_stock(solution: dict) -> dict:
    """The stock at each stage of the network at the end of each month (bikes)."""
    stages = {"Plants": F, "Central warehouse": [CENTRAL], "Regional warehouses": REGIONAL,
              "Local warehouses": LOCAL}
    return {stage: [sum(solution["stock"][i, t] for i in nodes) for t in solution["months"]]
            for stage, nodes in stages.items()}


def _node_month(solution: dict, i: str, t: str, node_capacity: dict = K_n) -> str:
    """The label of a node in the network of one month: its stock at the end of the
    month and, by kind of node, what it assembles, receives or delivers."""
    if i == RAIL_TERMINAL:
        return f"{_node_name(i)}<br>holds no stock"
    lines = [_node_name(i)]
    if i in F:
        lines.append(f"assembled in {t}: {_number(solution['assembly'][i, t])} bikes")
    if i in node_capacity:
        lines.append(f"received in {t}: {_number(figures._arriving(solution, i, t))} bikes "
                     f"(node capacity {_number(node_capacity[i])})")
    if i in SHARE:
        lines += [f"deliveries in {t}: {_number(solution['deliveries'][i, t])} bikes",
                  f"backorders at the end of {t}: {_number(solution['backorders'][i, t])} bikes"]
    lines.append(f"stock at the end of {t}: {_number(solution['stock'][i, t])} bikes")
    return "<br>".join(lines)


def _flow_network(solution: dict, node_capacity: dict = K_n):
    """The network with the flow on each arc, one month at a time, with a dropdown
    of the months: an arc whose capacity is full in red, an arc with no flow in
    light grey; the data of each node and arc in the month in its label."""
    arc_list, options = solution["arcs"], {}
    for t in solution["months"]:
        full = figures.full_arcs(solution, t)
        flow = {a: solution["flow"][a, t] for a in range(len(arc_list))}
        options[t] = dict(
            title=f"Plan of M3 in {t}: flow on each arc (bikes)", full=full,
            idle=[a for a, v in flow.items() if v <= TOL], arc_text={a: _number(v) for a, v in flow.items()},
            arc_hover={a: f"{_arc_label(a, arc)}<br>flow in {t}: {_number(flow[a])} bikes<br>arc capacity "
                          f"{_number(arc['capacity'])} bikes/month" + (", full" if a in full else "")
                       for a, arc in enumerate(arc_list)},
            node_hover={i: _node_month(solution, i, t, node_capacity) for i in NODES})
    return interactive.network(NODES, arc_list, options, first="May")


def _assembly_figure(solution: dict, capacity: dict = K):
    """The bikes that each plant assembles in each month against its capacity, with a
    dropdown of the plants and of the three plants together."""
    months = solution["months"]
    rows = {f: [solution["assembly"][f, t] for t in months] for f in F}
    colours = {f: interactive.colour(COLOURS[f]) for f in F}
    options = {f: interactive.bars(months, {f: rows[f]}, colours, f"Assembly of {f.lower()} in each month (bikes)",
                                   line=[capacity[f][t] for t in months], line_label="capacity", inside=True)
               for f in F}
    options["All plants"] = interactive.bars(
        months, rows, colours, "Assembly of the three plants in each month (bikes)",
        line=[sum(capacity[f][t] for f in F) for t in months], line_label="capacity of the three plants")
    return interactive.dropdown_figure(options)


def _stock_figure(solution: dict):
    """The stock at each stage of the network at the end of each month, stacked."""
    return interactive.bars(solution["months"], stage_stock(solution),
                            {s: interactive.colour(c) for s, c in figures.STAGE_COLOURS.items()},
                            "Stock at each stage at the end of the month (bikes)")


def _prices_figure(solution: dict, node_capacity: dict = K_n):
    """The shadow prices of the capacities that are full in each month, with a
    dropdown of the months."""
    full = {t: figures.full_capacities(solution, t, NODES, K_h_node, node_capacity) for t in solution["months"]}
    most = max(len(p) for p in full.values())
    return interactive.dropdown_figure(
        {t: interactive.horizontal_bars([name.split(" (")[0] for name, _ in p], [v for _, v in p],
                                        [name for name, _ in p], f"Shadow prices of the full capacities in {t} (€/bike)",
                                        "€/bike", unit="€/bike", empty=f"No capacity is full in {t}", rows=most)
         for t, p in full.items()}, first="May")


def _routes(solution: dict) -> list:
    """The arcs to regional warehouse 2 and to local warehouse 3 (Valencia)."""
    arc_list = solution["arcs"]
    return entering("Regional warehouse 2", arc_list) + entering("Local warehouse 3", arc_list)


def _route_table(solution: dict) -> pd.DataFrame:
    arc_list, months = solution["arcs"], solution["months"]
    return pd.DataFrame({t: {f"{a + 1}. {arc_name(arc_list[a])}": solution["flow"][a, t] for a in _routes(solution)}
                         for t in months}).rename_axis("Routes to regional warehouse 2 and Valencia (bikes)")


def _route_figure(solution: dict, node_capacity: dict = K_n):
    """The flow on the routes to regional warehouse 2 and to Valencia in each month,
    stacked by arc, with a dropdown of the two destinations; at regional warehouse
    2, its node capacity and its stock at the end of the month."""
    arc_list, months = solution["arcs"], solution["months"]
    # one colour for each route, none red: red marks a full arc capacity
    colours = iter(["tab:blue", "tab:orange", "tab:green", "tab:brown", "tab:purple"])
    options = {}
    for node, name in (("Regional warehouse 2", "regional warehouse 2 (Getafe)"),
                       ("Local warehouse 3", "local warehouse 3 (Valencia)")):
        rows = {f"arc {a + 1}: {arc_name(arc_list[a])}": [solution["flow"][a, t] for t in months]
                for a in entering(node, arc_list)}
        limit = node_capacity.get(node)
        fig = interactive.bars(
            months, rows, {row: interactive.colour(next(colours)) for row in rows},
            f"Flow on the routes to {name} (bikes)", line=limit,
            line_label=f"node capacity {_number(limit)}" if limit else "")
        if node == "Regional warehouse 2":
            # the colour of the regional warehouses in the stock at each stage
            name_stock = "stock of regional warehouse 2 at the end of the month"
            fig.add_scatter(x=months, y=[solution["stock"][node, t] for t in months], mode="lines+markers",
                            name=name_stock, line=dict(color=interactive.colour(figures.STAGE_COLOURS[
                                "Regional warehouses"]), width=2), marker_size=8,
                            hovertemplate=f"{name_stock}<br>%{{x}}: %{{y:,.0f}} bikes<extra></extra>")
        options[f"Routes to {name}"] = fig
    return interactive.dropdown_figure(options)


SEVILLE = "Local warehouse 4"


def _seville_figure(solution: dict):
    """The orders of Seville (local warehouse 4) in each month, the bikes delivered
    and the orders still pending at the end of the month."""
    import plotly.graph_objects as go

    months = solution["months"]
    rows = _seville_rows(solution)
    fig = go.Figure()
    # the orders without fill, the deliveries in the colour of the local warehouses
    # in the stock at each stage, and the pending orders in a colour of their own:
    # red marks a full capacity
    styles = {"orders": dict(marker_color="white", marker_line=dict(color="black", width=1)),
              "delivered": dict(marker_color=interactive.colour(figures.STAGE_COLOURS["Local warehouses"])),
              "pending at the end of the month": dict(marker_color=interactive.colour("tab:pink"))}
    for (label, values), style in zip(rows.items(), styles.values()):
        fig.add_bar(x=months, y=values, name=label, **style,
                    hovertemplate=f"{label}<br>%{{x}}: %{{y:,.0f}} bikes<extra></extra>")
    fig.update_layout(**interactive.LAYOUT, barmode="group", height=interactive.MONTH_HEIGHT,
                      title=dict(text="Seville (local warehouse 4): orders, deliveries and pending orders (bikes)",
                                 font_size=14),
                      yaxis=dict(title="bikes", range=[0, 1.15 * max(max(v) for v in rows.values())]))
    interactive._legend_below(fig)
    return fig


def _seville_rows(solution: dict) -> dict:
    months = solution["months"]
    return {"orders": [SHARE[SEVILLE] * DEMAND[t] for t in months],
            "delivered": [solution["deliveries"][SEVILLE, t] for t in months],
            "pending at the end of the month": [solution["backorders"][SEVILLE, t] for t in months]}


def _solved(data: dict, heading: str) -> dict | None:
    """Solve M3 with the data given and print its cost and whether other plans have
    the same cost, or that there is no plan."""
    solution = solve(**data)
    if solution is None:
        _say(f"{heading}: the model has no solution: no plan delivers every order by the end of June within "
              "the capacities of the network.")
        return None
    _say(f"{heading}: optimal plan, cost {_number(solution['cost'], 2)} €.")
    if not only_plan(**data):
        _say(SEVERAL)
    return solution


def _report(data: dict, heading: str, prices: bool = True, arc_flow: bool = False,
            show_tables: bool = False) -> dict | None:
    """Solve M3 with the data given and show its cost and whether other plans have
    the same cost; then the plan in figures or, with ``show_tables``, in tables:
    the flows on the network, one month at a time; with ``arc_flow``, the flow on
    one arc in each month; the assembly, the stock and, with ``prices``, the shadow
    prices of the full capacities."""
    solution = _solved(data, heading)
    if solution is None:
        return None
    if show_tables:
        _tables(solution)
        if prices:
            _prices(solution)
        return solution
    node_capacity = data.get("node_capacity", K_n)
    interactive.show(_flow_network(solution, node_capacity))
    if arc_flow:
        interactive.show(arc_flow_selector(solution))
    interactive.show(_assembly_figure(solution, data.get("capacity", K)))
    interactive.show(_stock_figure(solution))
    if prices:
        interactive.show(_prices_figure(solution, node_capacity))
    return solution


def arc_flow_figure(solution: dict, a: int):
    """A Plotly figure of the flow on arc ``a`` in each month, with its arc
    capacity as a dashed line: a month in which the capacity is full in red, as
    in the network."""
    import plotly.graph_objects as go

    arc = solution["arcs"][a]
    months = solution["months"]
    flows = [solution["flow"][a, t] for t in months]
    full = [v > TOL and abs(v - arc["capacity"]) < TOL for v in flows]
    fig = go.Figure(go.Bar(
        x=months, y=flows, marker_color=[interactive.FULL if f else figures.INK for f in full],
        text=[_number(v) for v in flows], textposition="outside",
        customdata=["arc capacity full" if f else f"{_number(arc['capacity'] - v)} bikes available" for v, f in
                    zip(flows, full)],
        hovertemplate="%{x}: %{y:,.0f} bikes (%{customdata})<extra></extra>", showlegend=False))
    fig.add_hline(y=arc["capacity"], line_dash="dash", line_color="black", line_width=1,
                  annotation_text=f"arc capacity {_number(arc['capacity'])}", annotation_position="top left")
    fig.update_layout(**interactive.LAYOUT, height=interactive.MONTH_HEIGHT,
                      title=dict(text=f"Flow on arc {a + 1} ({arc_name(arc)}, {arc['mode'].lower()}) in each month "
                                      "(bikes)", font_size=14),
                      yaxis=dict(title="bikes", range=[0, 1.15 * max(arc["capacity"], max(flows))]))
    return fig


def arc_flow_selector(solution: dict, first: int = RAIL_ARC):
    """The figure of the flow on one arc in each month, with a dropdown of the
    arcs; the plan is not solved again when the arc changes."""
    label = lambda a, arc: f"{a + 1}. {arc_name(arc)}" + (" (rail)" if arc["mode"] == RAIL else "")  # noqa: E731
    return interactive.dropdown_figure({label(a, arc): arc_flow_figure(solution, a)
                                        for a, arc in enumerate(solution["arcs"])},
                                       first=label(first, solution["arcs"][first]))


def network_plan(show_tables: bool = False) -> dict | None:
    """The plan with forecast 4, with the flows on the network; and, first, whether
    M2 has a plan for forecast 4."""
    if m2_has_no_solution():
        ordered = sum(DEMAND[t] for t in T[3:])
        assembled = sum(K[f][t] for f in F for t in T[3:])
        ending = sum(h_node_end[f] for f in F)
        _say(f"M2, with the plants and the central warehouse only, has no solution with the {FORECAST.lower()}: "
              f"from April to June {_number(ordered)} bikes are ordered and the plants can assemble "
              f"{_number(assembled)}, and the plants have to end June with {_number(ending)} bikes. At the end "
              f"of March {_number(ordered - assembled + ending)} bikes have to be in stock, and the plants and "
              f"the central warehouse can hold {_number(sum(K_h_node[f] for f in F) + K_h_node[CENTRAL])}.")
        _say()
    return _report({}, FORECAST, arc_flow=True, show_tables=show_tables)


def node_capacity_test(node_capacity: float = 280, show_tables: bool = False) -> dict | None:
    """The plan with forecast 4 and the node capacity of regional warehouse 2 changed:
    the flows on the routes to regional warehouse 2, with its stock, and to
    Valencia; and the orders, deliveries and pending orders of Seville."""
    _say(f"Node capacity of regional warehouse 2: {_number(node_capacity)} bikes/month.")
    limit = {"Regional warehouse 2": node_capacity}
    solution = _solved({"node_capacity": limit}, FORECAST)
    if solution is None:
        return None
    if show_tables:
        _display(_route_table(solution))
        _display(pd.DataFrame({t: {"Regional warehouse 2": solution["stock"]["Regional warehouse 2", t]}
                               for t in solution["months"]}).rename_axis("Stock at the end of the month (bikes)"))
        _display(pd.DataFrame(_seville_rows(solution), index=solution["months"]).T
                 .rename(index=str.capitalize).rename_axis("Seville, local warehouse 4 (bikes)"))
        return solution
    interactive.show(_route_figure(solution, limit))
    interactive.show(_seville_figure(solution))
    return solution


# ---------------------------------------------------------------------------
# The minimum cost flow problem of one month within the plan of M3: an analysis
# of the plan, not a version of the model (distribution_network.md §7)
# ---------------------------------------------------------------------------

SUPPLY_NODE, TRANSHIPMENT_NODE, DEMAND_NODE = "supply node", "transhipment node", "demand node"


def net_supply(solution: dict, month: str) -> dict:
    """The net supply q[i] of each node in a month of a plan of M3 (bikes): the stock
    at the start of the month, plus what the node assembles, less what it delivers
    and its stock at the end of the month. Positive at a supply node, negative at a
    demand node."""
    k = T.index(month)
    q = {}
    for i in NODES:
        before = h_node_0[i] if k == 0 else solution["stock"][i, T[k - 1]]
        q[i] = (before + solution["assembly"].get((i, month), 0) - solution["deliveries"].get((i, month), 0)
                - solution["stock"][i, month])
        q[i] = 0.0 if abs(q[i]) < TOL else q[i]
    return q


def node_kind(q: float) -> str:
    """The kind of a node in the minimum cost flow problem of a month, from its net supply."""
    return SUPPLY_NODE if q > TOL else (DEMAND_NODE if q < -TOL else TRANSHIPMENT_NODE)


def transport_cost(solution: dict, month: str) -> float:
    """The transport cost of a plan of M3 in a month (EUR)."""
    return sum(arc["cost"] * solution["flow"][a, month] for a, arc in enumerate(solution["arcs"]))


def min_cost_flow(supply: dict, arc_list: list = ARCS, node_capacity: dict = K_n) -> dict | None:
    """The minimum cost flow problem of one month on the network of M3: the net
    supply of each node given (bikes), the arc capacities, the node capacities and
    the transport cost as objective. Returns the transport cost (EUR) and the flow
    on each arc (bikes), or None if it has no solution."""
    model = pulp.LpProblem("min_cost_flow", pulp.LpMinimize)
    # x[a] = bikes shipped on arc a in the month
    x = {a: model.add_variable(f"x_{a}", lowBound=0, upBound=arc["capacity"]) for a, arc in enumerate(arc_list)}
    model += pulp.lpSum(arc["cost"] * x[a] for a, arc in enumerate(arc_list))
    for i in supply:
        # Flow balance: what leaves the node less what enters it is its net supply
        model += (pulp.lpSum(x[a] for a in leaving(i, arc_list)) - pulp.lpSum(x[a] for a in entering(i, arc_list))
                  == supply[i], f"balance_{_key(i)}")
    for i, capacity in node_capacity.items():
        model += (pulp.lpSum(x[a] for a in entering(i, arc_list)) <= capacity, f"node_capacity_{_key(i)}")
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    flow = {a: 0.0 if abs(v.value()) < TOL else v.value() for a, v in x.items()}
    return {"cost": pulp.value(model.objective), "flow": flow}


def month_problem(month: str, solution: dict | None = None) -> dict:
    """The minimum cost flow problem of one month taken from the optimal plan of M3:
    the net supply and the kind of each node, and its solution, with the transport
    cost and the flows of M3 in that month to compare."""
    solution = solution or solve()
    q = net_supply(solution, month)
    flows = min_cost_flow(q)
    return {"month": month, "supply": q, "kind": {i: node_kind(v) for i, v in q.items()},
            "cost": flows["cost"], "flow": flows["flow"], "m3 cost": transport_cost(solution, month),
            "m3 flow": {a: solution["flow"][a, month] for a in range(len(ARCS))}}


# The colour of each kind of node, as in figure F32a of the presentation of T3
KIND_FILL = {SUPPLY_NODE: "#C6DDDF", TRANSHIPMENT_NODE: figures.FILL, DEMAND_NODE: "#8FB9C0"}


def month_flows(show_tables: bool = False) -> dict:
    """The minimum cost flow problem of each month taken from the optimal plan of
    M3: the network with the kind and the net supply of each node and the flow on
    each arc, with a dropdown of the months; and its transport cost against that of
    M3 in each month. With ``show_tables``, the same in tables. Returns the problem
    of each month."""
    solution = solve()
    problems = {t: month_problem(t, solution) for t in T}
    if show_tables:
        _display(pd.DataFrame({t: {i: p["supply"][i] for i in NODES} for t, p in problems.items()})
                 .rename_axis("Net supply q (bikes)"))
        _display(pd.DataFrame({t: {i: p["kind"][i] for i in NODES} for t, p in problems.items()})
                 .rename_axis("Kind of node"))
        _display(pd.DataFrame({t: {f"{a + 1}. {arc_name(arc)}": p["flow"][a] for a, arc in enumerate(ARCS)}
                               for t, p in problems.items()}).rename_axis("Flow on each arc (bikes)"))
    else:
        options = {}
        for t, p in problems.items():
            flow = p["flow"]
            full = [a for a, arc in enumerate(ARCS) if flow[a] > TOL and abs(flow[a] - arc["capacity"]) < 1e-6]
            options[t] = dict(
                title=f"Minimum cost flow problem of {t}: flow on each arc (bikes)", full=full,
                idle=[a for a, v in flow.items() if v <= TOL], arc_text={a: _number(v) for a, v in flow.items()},
                fill={i: KIND_FILL[k] for i, k in p["kind"].items()},
                arc_hover={a: f"{_arc_label(a, arc)}<br>flow in {t}: {_number(flow[a])} bikes<br>arc capacity "
                              f"{_number(arc['capacity'])} bikes/month" + (", full" if a in full else "")
                           for a, arc in enumerate(ARCS)},
                node_hover={i: f"{_node_name(i)}<br>{p['kind'][i]}<br>net supply q in {t}: {_number(p['supply'][i])} "
                               "bikes" for i in NODES})
        interactive.show(interactive.network(NODES, ARCS, options, first="May", legend=KIND_FILL))
    _display(pd.DataFrame({t: {"Minimum cost flow problem (€)": _number(p["cost"], 2),
                               "Plan of M3 (€)": _number(p["m3 cost"], 2),
                               "Same flow on every arc": "yes" if all(abs(p["flow"][a] - p["m3 flow"][a]) < 1e-6
                                                                     for a in p["flow"]) else "no"}
                           for t, p in problems.items()}).rename_axis("Transport cost of the month"))
    return problems
