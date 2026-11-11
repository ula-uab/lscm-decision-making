"""M3 · Distribution network (distribution_network.md): the model of
central_warehouse.md (M2) written on a network given as a list of arcs, with
regional and local warehouses, a rail terminal, transport costs, arc capacities
and node capacities, written with PuLP and solved with HiGHS; and what the
notebook distribution_network.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the nodes, the list of arcs and forecast 4;
2. ``network_plan``: the plan with forecast 4, with the flows of one month;
3. ``rail_capacity_test``, ``rail_rate_test`` and ``node_capacity_test``: the plan
   when one datum changes.

Each one shows figures or, with ``show_tables``, the same data in tables.

The arcs are dicts with origin, destination, mode, distance (km), capacity
(bikes/month) and transport cost (EUR/bike), as in ``data.arcs``; an arc is
referred to by its position in the list. Node data are dicts by node.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .central_warehouse import SEVERAL, only_optimal
from .data import (ARCS, CENTRAL, F, FORECAST_4, K, K_h_node, K_n, LOCAL, NODES, PLACES, RAIL, RAIL_TERMINAL,
                   REGIONAL, SHARE, TRANSPORT_RATE, T, arcs as make_arcs, b_0, b_max, c, c_b, c_h_node, h_node_0,
                   h_node_end)
from .model import TOL, _constraints, _optimal
from . import figures
from .show import _display, _european_axes, _light, _number

FORECAST = "Forecast 4"                   # M3 is solved with forecast 4
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
    print(f"Transport rate (€/(bike·km)): road {_number(TRANSPORT_RATE['Road'], 3)}; "
          f"rail {_number(TRANSPORT_RATE['Rail'], 3)}.")
    orders = {i: [SHARE[i] * DEMAND[t] for t in T] for i in LOCAL}
    if not show_tables:
        figures.places_map([(_kind(i), *PLACES[i]) for i in NODES], "Places of the nodes of the network of M3")
        figures.network(NODES, range(len(ARCS)), {i: figures.data_text(i, stock=True) for i in NODES},
                        {a: figures.arc_text(arc) for a, arc in enumerate(ARCS)},
                        "Data of M3. Plants: unit assembly cost · capacity; holding cost · storage capacity; initial "
                        "stock → required final stock.\nWarehouses: holding cost · storage capacity"
                        + ("; each one starts and ends the six months with no stock" if figures.warehouses_empty(NODES)
                           else "") + ". Arcs: transport cost (€/bike) · arc capacity (bikes/month).",
                        arc_list=ARCS)
        figures.orders_figure({f"{i} ({PLACES[i][0]}), {_number(100 * SHARE[i])} %": orders[i] for i in LOCAL},
                              f"Orders of each local warehouse in each month: its share of {FORECAST.lower()}",
                              ylabel="Orders (bikes/month)")
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
    for i in NODES:
        if i != RAIL_TERMINAL and any(solution["storage price"][i, t] for t in months):
            rows[f"Storage capacity, {i}"] = {t: solution["storage price"][i, t] for t in months}
    if rows:
        print(PRICES)
        _display(pd.DataFrame(rows).T.rename_axis("Capacity"))


def stage_stock(solution: dict) -> dict:
    """The stock at each stage of the network at the end of each month (bikes)."""
    stages = {"Plants": F, "Central warehouse": [CENTRAL], "Regional warehouses": REGIONAL,
              "Local warehouses": LOCAL}
    return {stage: [sum(solution["stock"][i, t] for i in nodes) for t in solution["months"]]
            for stage, nodes in stages.items()}


def _network_text(solution: dict, month: str) -> dict:
    """Under each node, its stock at the end of the month; at each local warehouse,
    also its deliveries and its backorders."""
    text = {i: f"stock {_number(solution['stock'][i, month])}" for i in NODES if i != RAIL_TERMINAL}
    for i in LOCAL:
        text[i] += (f" · deliveries {_number(solution['deliveries'][i, month])} · "
                    f"backorders {_number(solution['backorders'][i, month])}")
    return text


@_light
def _stock_and_prices(solution: dict, month: str, node_capacity: dict, prices: bool = True) -> None:
    """The stock at each stage of the network; with ``prices``, beside it, the shadow
    prices of the capacities that are full in the month of the form."""
    months = solution["months"]
    if prices:
        fig, (left, right) = plt.subplots(1, 2, figsize=(15, 4.2), gridspec_kw={"width_ratios": [1, 1.25]})
        figures.shadow_prices(right, figures.full_capacities(solution, month, NODES, K_h_node, node_capacity), month)
    else:
        fig, left = plt.subplots(figsize=(7.5, 4.2))
    figures.stage_stock(left, stage_stock(solution), months)
    left.set_title("Stock at each stage of the network", fontsize=10)
    _european_axes(fig)
    fig.tight_layout()
    plt.show()


def _routes(solution: dict) -> list:
    """The arcs to regional warehouse 2 and to local warehouse 3 (Valencia)."""
    arc_list = solution["arcs"]
    return entering("Regional warehouse 2", arc_list) + entering("Local warehouse 3", arc_list)


def _route_table(solution: dict) -> pd.DataFrame:
    arc_list, months = solution["arcs"], solution["months"]
    return pd.DataFrame({t: {f"{a + 1}. {arc_name(arc_list[a])}": solution["flow"][a, t] for a in _routes(solution)}
                         for t in months}).rename_axis("Routes to regional warehouse 2 and Valencia (bikes)")


@_light
def _route_figure(solution: dict) -> None:
    """The flow on each route to regional warehouse 2 and to Valencia in each month,
    in grouped bars, with the arc capacity of each route."""
    arc_list, months = solution["arcs"], solution["months"]
    routes = _routes(solution)
    fig, ax = plt.subplots(figsize=(11, 4.8))
    colours = plt.get_cmap("tab10")
    width = 0.8 / len(routes)
    top = max(max(solution["flow"][a, t] for a in routes for t in months), 1) * 1.2
    for k, a in enumerate(routes):
        x = [i + (k - (len(routes) - 1) / 2) * width for i in range(len(months))]
        values = [solution["flow"][a, t] for t in months]
        arc = arc_list[a]
        ax.bar(x, values, width * 0.92, color=colours(k),
               label=f"arc {a + 1}: {arc_name(arc)} (arc capacity {_number(arc['capacity'])})")
        for xi, v in zip(x, values):
            ax.text(xi, v + top * 0.01, _number(v), ha="center", va="bottom", fontsize=6.5)
    ax.set_ylim(0, top)
    ax.set_xticks(range(len(months)), months)
    ax.set_ylabel("Flow (bikes/month)")
    ax.set_title("Flow on the routes to regional warehouse 2 (Getafe) and to local warehouse 3 (Valencia)",
                 fontsize=10)
    ax.legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    _european_axes(fig)
    fig.tight_layout()
    plt.show()


def _report(data: dict, heading: str, month: str = "May", prices: bool = True, routes: bool = False,
            show_tables: bool = False) -> dict | None:
    """Solve M3 with the data given and show its cost and whether other plans have
    the same cost; then the plan in figures or, with ``show_tables``, in tables:
    with ``routes``, the flows on the routes to regional warehouse 2 and Valencia;
    the flows of one month on the network, the assembly, the stock and, with
    ``prices``, the shadow prices of the full capacities."""
    if month not in T:
        raise ValueError(f"The month must be one of {', '.join(T)}.")
    solution = solve(**data)
    if solution is None:
        print(f"{heading}: the model has no solution: no plan delivers every order by the end of June within "
              "the capacities of the network.")
        return None
    print(f"{heading}: optimal plan, cost {_number(solution['cost'], 2)} €.")
    if not only_plan(**data):
        print(SEVERAL)
    if show_tables:
        if routes:
            _display(_route_table(solution))
        _tables(solution)
        if prices:
            _prices(solution)
        return solution
    if routes:
        _route_figure(solution)
    figures.flow_network(solution, month, NODES, _network_text(solution, month),
                         f"Plan of M3 in {month}. On each arc, its flow (bikes). Under each node, its stock at the end "
                         f"of {month} (bikes);\nat each local warehouse, also its deliveries in {month} and its "
                         f"backorders at the end of {month} (bikes).")
    figures.assembly_figure(solution["assembly"], data.get("capacity", K), solution["months"], F,
                            "Assembly of each plant in each month and its capacity")
    _stock_and_prices(solution, month, data.get("node_capacity", K_n), prices)
    return solution


def network_plan(month: str = "May", show_tables: bool = False) -> dict | None:
    """The plan with forecast 4, with the flows of one month on the network; and,
    first, whether M2 has a plan for forecast 4."""
    if m2_has_no_solution():
        ordered = sum(DEMAND[t] for t in T[3:])
        assembled = sum(K[f][t] for f in F for t in T[3:])
        ending = sum(h_node_end[f] for f in F)
        print(f"M2, with the plants and the central warehouse only, has no solution with {FORECAST.lower()}: "
              f"from April to June {_number(ordered)} bikes are ordered and the plants can assemble "
              f"{_number(assembled)}, and the plants have to end June with {_number(ending)} bikes. At the end "
              f"of March {_number(ordered - assembled + ending)} bikes have to be in stock, and the plants and "
              f"the central warehouse can hold {_number(sum(K_h_node[f] for f in F) + K_h_node[CENTRAL])}.")
        print()
    return _report({}, FORECAST, month, show_tables=show_tables)


def rail_capacity_test(rail_capacity: float = 400, month: str = "May", show_tables: bool = False) -> dict | None:
    """The plan with forecast 4 and the arc capacity of arc 6, the rail arc, changed."""
    arc_list = [dict(arc) for arc in ARCS]
    arc_list[RAIL_ARC]["capacity"] = rail_capacity
    print(f"Arc capacity of arc 6 (rail): {_number(rail_capacity)} bikes/month.")
    return _report({"arc_list": arc_list}, FORECAST, month, prices=False, routes=True, show_tables=show_tables)


def rail_rate_test(rail_rate: float = 0.006, month: str = "May", show_tables: bool = False) -> dict | None:
    """The plan with forecast 4 and the transport rate of rail changed: the transport
    cost of the rail arc is its distance times that rate."""
    arc_list = make_arcs({**TRANSPORT_RATE, RAIL: rail_rate})
    print(f"Transport rate of rail: {_number(rail_rate, 4)} €/(bike·km); transport cost of the rail arc: "
          f"{_number(arc_list[RAIL_ARC]['cost'], 2)} €/bike.")
    return _report({"arc_list": arc_list}, FORECAST, month, prices=False, routes=True, show_tables=show_tables)


def node_capacity_test(node_capacity: float = 280, month: str = "May", show_tables: bool = False) -> dict | None:
    """The plan with forecast 4 and the node capacity of regional warehouse 2 changed."""
    print(f"Node capacity of regional warehouse 2: {_number(node_capacity)} bikes/month.")
    return _report({"node_capacity": {"Regional warehouse 2": node_capacity}}, FORECAST, month, prices=False,
                   routes=True, show_tables=show_tables)
