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
from .show import COLOURS, SHORT, _display, _euros, _european_axes, _light, _number

FORECAST = "Forecast 4"                   # M3 is solved with forecast 4
DEMAND = FORECAST_4
RAIL_ARC = next(a for a, arc in enumerate(ARCS) if arc["mode"] == RAIL)

# Position of each node in the figure of the network, and where its label goes:
# the map of Spain, with nodes that are close to each other moved apart
POSITION = {
    "Plant 1": (-2.9, 43.1, "left"), "Plant 2": (-1.3, 43.1, "right"), "Plant 3": (0.6, 39.9, "right"),
    CENTRAL: (-0.9, 41.7, "right"), RAIL_TERMINAL: (-3.0, 41.0, "left"),
    "Regional warehouse 1": (2.3, 41.5, "right"), "Regional warehouse 2": (-3.9, 39.9, "left"),
    "Local warehouse 1": (3.0, 42.4, "right"), "Local warehouse 2": (1.2, 40.8, "right"),
    "Local warehouse 3": (-0.6, 39.0, "right"), "Local warehouse 4": (-5.5, 37.5, "right"),
}


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
    """The model of M3, not solved. ``share`` gives the nodes with demand and the share
    of the demand that each one receives. Returns the model, a dict of its variables
    by kind ("p" by (f, t); "x" by (a, t); "h" by (i, t); "s", "b" by (i, t) at the
    nodes with demand) and the cost expression."""
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
            model += (h[i, months[-1]] >= final[i], f"ending_stock_{_key(i)}")
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
    node, and the deliveries and backorders of each node with demand, by month
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

def show_data() -> None:
    """Tables 1 to 4 of distribution_network.md: the nodes and their places, the
    list of arcs, the data of each node and forecast 4."""
    _display(pd.DataFrame({i: {"Place": PLACES[i][0], "Latitude": _number(PLACES[i][1], 4),
                               "Longitude": _number(PLACES[i][2], 4)}
                           for i in NODES}).T.rename_axis("Node"))
    print(f"Transport rate (€/(bike·km)): road {_number(TRANSPORT_RATE['Road'], 3)}; "
          f"rail {_number(TRANSPORT_RATE['Rail'], 3)}.")
    _display(pd.DataFrame([{"Arc": a + 1, "Origin": arc["origin"], "Destination": arc["destination"],
                            "Mode": arc["mode"], "Distance (km)": arc["km"],
                            "Transport cost (€/bike)": arc["cost"], "Arc capacity (bikes/month)": arc["capacity"]}
                           for a, arc in enumerate(ARCS)]).set_index("Arc"))
    _display(pd.DataFrame({i: {"Holding cost (€/(bike·month))": c_h_node[i], "Storage capacity (bikes)": K_h_node[i],
                               "Stock at the end of December (bikes)": h_node_0[i],
                               "Required ending stock (bikes)": h_node_end[i],
                               "Node capacity (bikes/month)": K_n.get(i, "—")} for i in NODES}).T.rename_axis("Node"))
    orders = {i: {t: SHARE[i] * DEMAND[t] for t in T} for i in LOCAL}
    orders[FORECAST] = DEMAND
    table = pd.DataFrame(orders).T
    table.insert(0, "Share", [f"{_number(100 * SHARE[i])} %" for i in LOCAL] + ["100 %"])
    _display(table.rename_axis("Orders (bikes/month)"))


def _flow_table(solution: dict) -> pd.DataFrame:
    arc_list, months = solution["arcs"], solution["months"]
    return pd.DataFrame({t: {f"{a + 1}. {arc_name(arc)}": solution["flow"][a, t] for a, arc in enumerate(arc_list)}
                         for t in months}).rename_axis("Flow on each arc (bikes)")


def _tables(solution: dict) -> None:
    months = solution["months"]
    _display(pd.DataFrame({t: {f: solution["assembly"][f, t] for f in F} for t in months})
             .rename_axis("Bikes assembled"))
    _display(_flow_table(solution))
    _display(pd.DataFrame({t: {i: solution["stock"][i, t] for i in NODES} for t in months})
             .rename_axis("Stock at the end of the month (bikes)"))
    rows = {}
    for i in SHARE:
        rows["Deliveries", i] = {t: solution["deliveries"][i, t] for t in months}
    for i in SHARE:
        rows["Backorders at the end of the month", i] = {t: solution["backorders"][i, t] for t in months}
    _display(pd.DataFrame(rows).T.rename_axis(["Bikes", "Local warehouse"]))


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
    """Left: the network on a map, with the flow on each arc in one month; an arc
    whose capacity is full is drawn in red. Right: stock at each level of the
    network at the end of each month."""
    arc_list, months = solution["arcs"], solution["months"]
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.3, 1]})
    lon = {i: POSITION[i][0] for i in NODES}
    lat = {i: POSITION[i][1] for i in NODES}
    top = max([solution["flow"][a, month] for a in range(len(arc_list))] + [1])
    for a, arc in enumerate(arc_list):
        i, j = arc["origin"], arc["destination"]
        flow = solution["flow"][a, month]
        full = flow > TOL and abs(flow - arc["capacity"]) < 1e-6
        colour = SHORT if full else ("0.25" if flow > TOL else "0.8")
        left.annotate("", xy=(lon[j], lat[j]), xytext=(lon[i], lat[i]),
                      arrowprops=dict(arrowstyle="-|>", color=colour, lw=0.8 + 4 * flow / top,
                                      ls="-" if arc["mode"] == "Road" else "--", shrinkA=6, shrinkB=6))
        if flow > TOL:
            left.annotate(_number(flow), ((lon[i] + lon[j]) / 2, (lat[i] + lat[j]) / 2), fontsize=8,
                          color=colour, ha="center", va="center",
                          bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
    for i in NODES:
        colour = COLOURS.get(i, "black" if i == RAIL_TERMINAL else "tab:gray")
        left.scatter(lon[i], lat[i], s=60, color=colour, marker="s" if i == RAIL_TERMINAL else "o", zorder=3)
        side = POSITION[i][2]
        left.annotate(f"{i}\n{PLACES[i][0]}", (lon[i], lat[i]), xytext=(7 if side == "right" else -7, 0),
                      textcoords="offset points", fontsize=7, ha="left" if side == "right" else "right", va="center")
    left.plot([], [], color="0.25", lw=2, label="road")
    left.plot([], [], color="0.25", lw=2, ls="--", label="rail")
    left.plot([], [], color=SHORT, lw=2, label="arc capacity full")
    left.set_title(f"Flow on each arc in {month} (bikes); positions follow the map, not to scale", fontsize=10)
    left.set_xlim(-8.5, 5.5)
    left.set_ylim(36.8, 43.8)
    left.axis("off")
    left.legend(fontsize=7, loc="lower right")

    levels = {"plants": F, "central warehouse": [CENTRAL], "regional warehouses": REGIONAL,
              "local warehouses": LOCAL}
    colours = {"plants": "tab:blue", "central warehouse": "tab:gray", "regional warehouses": "tab:olive",
               "local warehouses": "tab:cyan"}
    x = range(len(months))
    bottom = [0.0] * len(months)
    for level, nodes in levels.items():
        values = [sum(solution["stock"][i, t] for i in nodes) for t in months]
        right.bar(x, values, bottom=bottom, color=colours[level], width=0.7, label=level)
        bottom = [b + v for b, v in zip(bottom, values)]
    right.set_xticks(list(x), months)
    right.set_ylabel("Bikes at the end of the month")
    right.set_ylim(0, max(500, max(bottom) * 1.15))
    right.set_title("Stock at each level of the network", fontsize=10)
    right.legend(fontsize=7, loc="upper right")
    right.spines[["top", "right"]].set_visible(False)
    _european_axes(fig)
    plt.show()


def _report(data: dict, heading: str, month: str = "May", prices: bool = True) -> dict | None:
    """Solve M3 with the data given and show the plan and its cost, whether other
    plans have the same cost, the shadow prices of the full capacities and the figure."""
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
    _tables(solution)
    if prices:
        _prices(solution)
    _figure(solution, month)
    return solution


def network_plan(month: str = "May") -> dict | None:
    """The plan with forecast 4, with the flows of one month on the map; and, first,
    whether M2 has a plan for forecast 4."""
    if m2_has_no_solution():
        print(f"M2, with the plants and the central warehouse only, has no solution with {FORECAST.lower()}: "
              f"from April to June {_number(sum(DEMAND[t] for t in T[3:]))} bikes are ordered, the plants can "
              f"assemble {_number(sum(K[f][t] for f in F for t in T[3:]))}, and the plants and the central "
              f"warehouse can hold {_number(sum(K_h_node[f] for f in F) + K_h_node[CENTRAL])}.")
        print()
    return _report({}, FORECAST, month)


def _route_summary(solution: dict | None) -> None:
    """Flows on the routes to regional warehouse 2 and to local warehouse 3 (Valencia)."""
    if solution is None:
        return
    arc_list, months = solution["arcs"], solution["months"]
    routes = entering("Regional warehouse 2", arc_list) + entering("Local warehouse 3", arc_list)
    _display(pd.DataFrame({t: {f"{a + 1}. {arc_name(arc_list[a])}": solution["flow"][a, t] for a in routes}
                           for t in months}).rename_axis("Routes to regional warehouse 2 and Valencia (bikes)"))


def rail_capacity_test(rail_capacity: float = 400, month: str = "May") -> dict | None:
    """The plan with forecast 4 and the arc capacity of the rail arc changed."""
    arc_list = [dict(arc) for arc in ARCS]
    arc_list[RAIL_ARC]["capacity"] = rail_capacity
    print(f"Arc capacity of the rail arc: {_number(rail_capacity)} bikes/month.")
    solution = solve(arc_list=arc_list)
    _route_summary(solution)
    return _report({"arc_list": arc_list}, FORECAST, month, prices=False)


def rail_rate_test(rail_rate: float = 0.006, month: str = "May") -> dict | None:
    """The plan with forecast 4 and the transport rate of rail changed: the transport
    cost of the rail arc is its distance times that rate."""
    arc_list = make_arcs({**TRANSPORT_RATE, RAIL: rail_rate})
    print(f"Transport rate of rail: {_number(rail_rate, 4)} €/(bike·km); transport cost of the rail arc: "
          f"{_number(arc_list[RAIL_ARC]['cost'], 2)} €/bike.")
    solution = solve(arc_list=arc_list)
    _route_summary(solution)
    return _report({"arc_list": arc_list}, FORECAST, month, prices=False)


def node_capacity_test(node_capacity: float = 280, month: str = "May") -> dict | None:
    """The plan with forecast 4 and the node capacity of regional warehouse 2 changed."""
    print(f"Node capacity of regional warehouse 2: {_number(node_capacity)} bikes/month.")
    data = {"node_capacity": {"Regional warehouse 2": node_capacity}}
    solution = solve(**data)
    _route_summary(solution)
    return _report(data, FORECAST, month, prices=False)
