"""M3 · Distribution network (distribution_network.md): the model of
central_warehouse.md (M2) written on a network given as a list of arcs, with
regional and local warehouses, a rail terminal, transport costs, arc capacities
and node capacities, written with PuLP and solved with HiGHS; and what the
notebook distribution_network.ipynb shows.

The notebook calls one function per step:

1. ``show_data``: the nodes, the list of arcs and forecast 4;
2. ``network_plan``: the plan with forecast 4, with the flows of one month;
3. ``rail_capacity_test``, ``rail_rate_test`` and ``node_capacity_test``: the plan
   when one datum changes;
4. ``month_flows`` and ``max_flows``: two analyses of the plan, not versions of the
   model: the minimum cost flow problem of one month, and the maximum flow to
   regional warehouse 2 and to Seville.

Each one shows figures or, with ``show_tables``, the same data in tables.

The arcs are dicts with origin, destination, mode, distance (km), capacity
(bikes/month) and transport cost (EUR/bike), as in ``data.arcs``; an arc is
referred to by its position in the list. Node data are dicts by node.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Patch
import pulp

from .central_warehouse import SEVERAL, only_optimal
from .data import (ARCS, CENTRAL, F, FORECAST_4, FORECAST_4_NAME, K, K_h_node, K_n, LOCAL, NODES, PLACES, RAIL,
                   RAIL_TERMINAL, REGIONAL, SHARE, TRANSPORT_RATE, T, arcs as make_arcs, b_0, b_max, c, c_b, c_h_node,
                   h_node_0, h_node_end)
from .model import TOL, _constraints, _optimal
from . import figures
from .show import SHORT, _display, _european_axes, _light, _number

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
                        text_colour=figures.INK, arc_list=ARCS)
        figures.orders_figure({f"{i} ({PLACES[i][0]}), {_number(100 * SHARE[i])} %": orders[i] for i in LOCAL},
                              f"{FORECAST}: orders of each local warehouse in each month, its share of the forecast",
                              ylabel="Orders (bikes/month)", capacity=sum(K[f]["Jan"] for f in F))
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
    # one colour for each route, none red: red marks a full arc capacity
    colours = ["tab:blue", "tab:orange", "tab:green", "tab:brown", "tab:purple"]
    width = 0.8 / len(routes)
    top = max(max(solution["flow"][a, t] for a in routes for t in months), 1) * 1.2
    for k, a in enumerate(routes):
        x = [i + (k - (len(routes) - 1) / 2) * width for i in range(len(months))]
        values = [solution["flow"][a, t] for t in months]
        arc = arc_list[a]
        ax.bar(x, values, width * 0.92, color=colours[k],
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
        print(f"M2, with the plants and the central warehouse only, has no solution with the {FORECAST.lower()}: "
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


# ---------------------------------------------------------------------------
# Two classical network problems within the plan of M3: analyses of the plan,
# not versions of the model (distribution_network.md §7)
# ---------------------------------------------------------------------------

SUPPLY_NODE, TRANSHIPMENT_NODE, DEMAND_NODE = "supply node", "transhipment node", "demand node"
DESTINATIONS = {"Regional warehouse 2": "Getafe", "Local warehouse 4": "Seville"}


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


def max_flow(destination: str, arc_list: list = ARCS, node_capacity: dict = K_n) -> dict:
    """The maximum flow problem of one month on the network of M3, from a fictitious
    origin o joined to the three plants by arcs with no capacity, to one destination
    node. Costs, stock and orders do not enter. Returns the maximum flow (bikes) and
    the capacities that limit it: those whose shadow price is not 0, as (kind, arc
    position or node, capacity)."""
    model = pulp.LpProblem("max_flow", pulp.LpMaximize)
    # y[f] = bikes from the origin o to plant f; x[a] = bikes on arc a; value = flow f
    y = {f: model.add_variable(f"y_{_key(f)}", lowBound=0) for f in F}
    x = {a: model.add_variable(f"x_{a}", lowBound=0) for a in range(len(arc_list))}
    value = model.add_variable("f", lowBound=0)
    model += value
    model += (pulp.lpSum(y.values()) == value, "balance_o")
    for i in NODES:
        into = pulp.lpSum(x[a] for a in entering(i, arc_list)) + (y[i] if i in F else 0)
        out = pulp.lpSum(x[a] for a in leaving(i, arc_list))
        # Flow balance: at the destination, what enters less what leaves is the flow f
        model += (into - out == (value if i == destination else 0), f"balance_{_key(i)}")
    for a, arc in enumerate(arc_list):
        model += (x[a] <= arc["capacity"], f"arc_capacity_{a}")
    for i, capacity in node_capacity.items():
        model += (pulp.lpSum(x[a] for a in entering(i, arc_list)) <= capacity, f"node_capacity_{_key(i)}")
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        raise RuntimeError("The maximum flow problem has no optimal solution.")
    cons = _constraints(model)
    limits = [("arc", a, arc["capacity"]) for a, arc in enumerate(arc_list) if abs(cons[f"arc_capacity_{a}"].pi) > TOL]
    limits += [("node", i, capacity) for i, capacity in node_capacity.items()
               if abs(cons[f"node_capacity_{_key(i)}"].pi) > TOL]
    return {"destination": destination, "value": pulp.value(model.objective), "limits": limits}


# The colour of each kind of node, as in figure F32a of the presentation of T3
KIND_FILL = {SUPPLY_NODE: "#C6DDDF", TRANSHIPMENT_NODE: figures.FILL, DEMAND_NODE: "#8FB9C0"}
# The fictitious origin of the maximum flow problem and its arcs: a colour that
# marks nothing else in the notebook, and dotted, so that they are not taken for
# part of the network
ORIGIN_COLOUR = "darkgoldenrod"
SEVILLE = "Local warehouse 4"


def _kind_handles() -> list:
    return [Patch(facecolor=KIND_FILL[k], edgecolor=figures.INK, label=k) for k in KIND_FILL]


def month_flows(month: str = "May", show_tables: bool = False) -> dict:
    """The minimum cost flow problem of one month taken from the optimal plan of M3:
    the network with the kind and the net supply of each node and the flow on each
    arc; and its transport cost against that of M3 in the month. With
    ``show_tables``, the same in two tables."""
    if month not in T:
        raise ValueError(f"The month must be one of {', '.join(T)}.")
    problem = month_problem(month)
    q, flow = problem["supply"], problem["flow"]
    same = all(abs(flow[a] - problem["m3 flow"][a]) < 1e-6 for a in flow)
    if show_tables:
        _display(pd.DataFrame({i: {"Net supply q (bikes)": q[i], "Kind of node": problem["kind"][i]} for i in NODES})
                 .T.rename_axis(f"Node, {month}"))
        _display(pd.DataFrame({f"{a + 1}. {arc_name(arc)}": {"Minimum cost flow problem": flow[a],
                                                             "Plan of M3": problem["m3 flow"][a]}
                               for a, arc in enumerate(ARCS)}).T.rename_axis(f"Flow on each arc in {month} (bikes)"))
    else:
        full = [a for a, arc in enumerate(ARCS) if flow[a] > TOL and abs(flow[a] - arc["capacity"]) < 1e-6]
        handles = _kind_handles() + [Line2D([], [], color=figures.INK, lw=1.2, label="road"),
                                     Line2D([], [], color=figures.INK, lw=1.2, ls=(0, (5, 3)), label="rail"),
                                     Line2D([], [], color=SHORT, lw=1.6, label="arc capacity full"),
                                     Line2D([], [], color=figures.IDLE, lw=1.2, label="no flow")]
        figures.network(NODES, range(len(ARCS)), {i: f"q = {_number(q[i])}" for i in NODES if i != RAIL_TERMINAL},
                        {a: _number(v) for a, v in flow.items()},
                        f"Minimum cost flow problem of {month}, from the plan of M3. On each arc, its flow (bikes). "
                        f"Under each node, its net supply q in {month} (bikes):\npositive at a supply node, negative "
                        "at a demand node and 0 at a transhipment node; at the rail terminal, which holds no stock, "
                        "it is always 0.",
                        full=full, idle=[a for a, v in flow.items() if v <= TOL], text_colour=figures.INK,
                        arc_list=ARCS, fill={i: KIND_FILL[k] for i, k in problem["kind"].items()}, handles=handles)
    print(f"Transport cost in {month}: minimum cost flow problem {_number(problem['cost'], 2)} €; plan of M3 "
          f"{_number(problem['m3 cost'], 2)} €. The flows are the same on every arc: {'yes' if same else 'no'}.")
    return problem


def _limit_text(limits: list) -> str:
    """The capacities that limit a maximum flow, in one sentence."""
    texts = [f"the node capacity of {where.lower()}, {_number(capacity)} bikes/month" if kind == "node" else
             f"the arc capacity of arc {where + 1} ({arc_name(ARCS[where])}), {_number(capacity)} bikes/month"
             for kind, where, capacity in limits]
    if len(texts) == 1:
        return f"It is limited by {texts[0]}."
    return (f"It is limited by {'; '.join(texts[:-1])}; and {texts[-1]}: together, "
            f"{_number(sum(capacity for *_, capacity in limits))} bikes/month.")


def _towards(destination: str) -> list:
    """The arcs on some path from the plants to the destination (positions)."""
    reached, ahead = set(F), list(F)
    while ahead:
        i = ahead.pop()
        for a in leaving(i, ARCS):
            if ARCS[a]["destination"] not in reached and ARCS[a]["origin"] != destination:
                reached.add(ARCS[a]["destination"])
                ahead.append(ARCS[a]["destination"])
    back, ahead = {destination}, [destination]
    while ahead:
        j = ahead.pop()
        for a in entering(j, ARCS):
            if ARCS[a]["origin"] not in back:
                back.add(ARCS[a]["origin"])
                ahead.append(ARCS[a]["origin"])
    return [a for a, arc in enumerate(ARCS) if arc["origin"] in reached and arc["destination"] in back
            and arc["origin"] != destination]


def _origin(ax) -> None:
    """The fictitious origin o, left of the plants, and its arcs to the top of each plant."""
    x, y, r = 60, 245, 15
    ax.add_patch(Circle((x, y), r, facecolor="white", edgecolor=ORIGIN_COLOUR, lw=1.4, ls=(0, (2, 2)), zorder=3))
    ax.text(x, y, "o", ha="center", va="center", fontsize=10, style="italic", color=ORIGIN_COLOUR, zorder=4)
    for (top, bend), side in zip(((52, 30), (174, 141), (392, 370)), (-1, -1, 1)):
        points = [(x, y + side * r), (x, bend), (330, bend), (330, top)]
        xs, ys = zip(*points)
        ax.plot(xs, ys, color=ORIGIN_COLOUR, lw=1.2, ls=(0, (1, 2)), zorder=2)
        ax.annotate("", xy=points[-1], xytext=points[-2],
                    arrowprops=dict(arrowstyle="-|>", color=ORIGIN_COLOUR, lw=1.2), zorder=2)


@_light
def _max_flow_figure(problem: dict, seville: dict, node_capacity: bool) -> None:
    """The network with the fictitious origin and the arc capacities of the arcs
    that lead to the destination, the capacities that limit the maximum flow in
    red; beside it, the orders of Seville in each month against the maximum flow
    to Seville."""
    destination = problem["destination"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(17.5, 7.0), gridspec_kw={"width_ratios": [3.3, 1]})
    towards = _towards(destination)
    full = [where for kind, where, _ in problem["limits"] if kind == "arc"]
    getafe = "Regional warehouse 2"
    text = {destination: "destination e"}
    if getafe in K_n:
        capacity = f"node capacity {_number(K_n[getafe])}" if node_capacity else "node capacity not applied"
        text[getafe] = " · ".join(filter(None, [text.get(getafe), capacity]))
    red = [where for kind, where, _ in problem["limits"] if kind == "node"]
    handles = [Line2D([], [], color=figures.INK, lw=1.2, label="road"),
               Line2D([], [], color=figures.INK, lw=1.2, ls=(0, (5, 3)), label="rail"),
               Line2D([], [], color=ORIGIN_COLOUR, lw=1.2, ls=(0, (1, 2)),
                      label="fictitious origin o and its arcs to the plants, with no capacity:\nnot part of the network"),
               Line2D([], [], color=SHORT, lw=1.6, label="capacity that limits the maximum flow"),
               Line2D([], [], color=figures.IDLE, lw=1.2, label="arc that does not lead to the destination")]
    figures.network(NODES, range(len(ARCS)), text, {a: _number(ARCS[a]["capacity"]) for a in towards},
                    f"Maximum flow problem of one month, from the fictitious origin o to "
                    f"{destination.lower()} ({DESTINATIONS[destination]}): {_number(problem['value'])} bikes.\n"
                    "On each arc, its arc capacity (bikes/month).",
                    full=full, idle=[a for a in range(len(ARCS)) if a not in towards], text_colour=figures.INK,
                    arc_list=ARCS, red_text=red, extra=_origin, handles=handles, ax=left)
    orders = [SHARE[SEVILLE] * DEMAND[t] for t in T]
    most = seville["value"]
    within = [min(v, most) for v in orders]
    above = [v - w for v, w in zip(orders, within)]
    # the colour of the orders of Seville in section 1
    right.bar(range(len(T)), within, 0.62, color=plt.get_cmap("Set2")(3), label="orders of Seville")
    right.bar(range(len(T)), above, 0.62, bottom=within, color=SHORT, label="orders above the maximum flow")
    for k, v in enumerate(orders):
        right.text(k, v + 4, _number(v), ha="center", va="bottom", fontsize=8)
    figures.step(right, T, [most] * len(T), color=figures.INK, lw=1.2, ls="--",
                 label=f"maximum flow to Seville in a month, {_number(most)} bikes")
    right.set_xticks(range(len(T)), T)
    right.set_ylim(0, max(max(orders), most) * 1.25)
    right.set_ylabel("Bikes/month")
    right.set_title("Orders of local warehouse 4 (Seville)\nand the maximum flow to Seville", fontsize=10)
    right.legend(fontsize=7.5, loc="upper left", frameon=False)
    right.spines[["top", "right"]].set_visible(False)
    _european_axes(fig)
    fig.tight_layout()
    plt.show()


def max_flows(destination: str = "Regional warehouse 2", node_capacity: bool = True,
              show_tables: bool = False) -> dict:
    """The maximum flow problem of one month on the network of M3, from a fictitious
    origin joined to the plants to one destination, with or without the node
    capacity of regional warehouse 2; and the orders of Seville in each month
    against the maximum flow to Seville. With ``show_tables``, the same in tables."""
    if destination not in DESTINATIONS:
        raise ValueError(f"The destination must be one of {', '.join(DESTINATIONS)}.")
    capacities = K_n if node_capacity else {}
    problem = max_flow(destination, node_capacity=capacities)
    seville = problem if destination == SEVILLE else max_flow(SEVILLE, node_capacity=capacities)
    for p in (problem,) if destination == SEVILLE else (problem, seville):
        print(f"Maximum flow in a month from the plants to {p['destination'].lower()} "
              f"({DESTINATIONS[p['destination']]}), {'with' if node_capacity else 'without'} the node capacity of "
              f"regional warehouse 2: {_number(p['value'])} bikes. {_limit_text(p['limits'])}")
    orders = {t: SHARE[SEVILLE] * DEMAND[t] for t in T}
    if show_tables:
        _display(pd.DataFrame({"Orders of Seville (bikes)": orders,
                               "Maximum flow to Seville (bikes)": {t: seville["value"] for t in T},
                               "Orders above the maximum flow (bikes)":
                                   {t: max(orders[t] - seville["value"], 0) for t in T}}).T.rename_axis("Month"))
    else:
        _max_flow_figure(problem, seville, node_capacity)
    return problem
