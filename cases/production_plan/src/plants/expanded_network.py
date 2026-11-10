"""Expanded network (expanded_network.md): after an expansion, the manufacturer
serves 46 retailers from 12 local warehouses and considers 8 candidate sites for
regional warehouses. Three selection problems on that network, each written with
PuLP and solved with HiGHS to its exact optimum:

- which local warehouse serves each retailer, a generalized assignment problem,
  with the rule and the transportation problem that the document compares with it;
- which candidate sites act as regional warehouses, a set covering problem, and the
  same sets written with "exactly one";
- the weekly routes of local warehouse 2 to its retailers, a set partitioning
  problem over the candidate routes, listed beforehand with their cost.

The notebook expanded_network.ipynb calls one function per step:

1. ``show_data``: the retailers, the local warehouses, the candidate sites and the
   distances and travel times;
2. ``assignment``: the four plans of the assignment, with the capacity of one local
   warehouse changed;
3. ``covering``: the regional warehouses for a maximum travel time, with "at least
   one" or "exactly one";
4. ``routes``: the weekly routes for a truck capacity, from the full list of
   candidate routes or from the short list.

M0 to M4 are the network before the expansion; this module does not use them.
"""

from __future__ import annotations

import itertools

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .data import (LOCAL_EXP, MAX_ROUTE_KM, MAX_TRAVEL_TIME, NODE_CAPACITY_YEAR, PLACES_EXP, RETAILERS_EXP, ROAD,
                   ROAD_KM_EXP, ROUTE_FIXED_COST, ROUTE_KM, ROUTE_KM_COST, ROUTE_NODES, ROUTE_RETAILERS,
                   ROUTE_WAREHOUSE, SITE_COST, SITES, TRANSPORT_RATE, TRAVEL_TIME, TRUCK_CAPACITY, WEEKLY_ORDERS,
                   YEARLY_ORDERS)
from .model import TOL, _optimal
from .show import SHORT, _display, _light, _number

SHORT_LIST_STOPS = 2           # the short list: the routes of one and of two retailers


def _solver():
    """HiGHS with no relative or absolute gap: every model is solved to its exact
    optimum."""
    return pulp.HiGHS(msg=False, gapRel=0, gapAbs=0)


def _binary(model, name: str):
    # In PuLP 4 cat="Binary" drops the bounds 0 and 1; written as an integer in [0, 1]
    return model.add_variable(name, lowBound=0, upBound=1, cat="Integer")


def _key(name: str) -> str:
    return name.replace(" ", "")


def place(node: str) -> str:
    """A node with its place: «Local warehouse 2 (Tarragona)»; a candidate site is
    named by its place."""
    return node if node in SITES else f"{node} ({PLACES_EXP[node][0]})"


def _only_selection(model, chosen: list, others: list, cost: float) -> bool:
    """True if no other selection of the binary variables has the optimal cost: the
    model, with the chosen selection excluded, has no solution or a dearer one.
    The model is changed."""
    model += (pulp.lpSum(chosen) - pulp.lpSum(others) <= len(chosen) - 1, "exclude_the_optimum")
    if not _optimal(model.solve(_solver())):
        return True
    return pulp.value(model.objective) > cost + 0.005          # EUR: the costs have cents


# ---------------------------------------------------------------------------
# Which local warehouse serves each retailer: generalized assignment
# ---------------------------------------------------------------------------

def transport_costs(km: dict = ROAD_KM_EXP, rate: float = TRANSPORT_RATE[ROAD]) -> dict:
    """The transport cost of each pair of local warehouse and retailer (EUR/bike), by
    (l, r): its road distance times the transport rate of road, rounded to the cent."""
    return {(l, r): round(km[l][k] * rate, 2) for l in km for k, r in enumerate(RETAILERS_EXP)}


COST = transport_costs()


def _plan(warehouse: dict, orders: dict, capacity: dict, cost: dict) -> dict:
    load = {l: sum(orders[r] for r in orders if warehouse[r] == l) for l in capacity}
    return {"warehouse": warehouse, "load": load, "over": [l for l in capacity if load[l] > capacity[l] + TOL],
            "cost": sum(cost[warehouse[r], r] * orders[r] for r in orders)}


def cheapest_plan(orders: dict = YEARLY_ORDERS, capacity: dict = NODE_CAPACITY_YEAR, cost: dict = COST) -> dict:
    """Each retailer at its cheapest local warehouse, whatever the capacities. Returns
    the warehouse of each retailer, the load of each warehouse (bikes/year), the
    warehouses whose load exceeds their capacity, and the cost (EUR/year)."""
    return _plan({r: min(capacity, key=lambda l: cost[l, r]) for r in orders}, orders, capacity, cost)


def rule_plan(orders: dict = YEARLY_ORDERS, capacity: dict = NODE_CAPACITY_YEAR, cost: dict = COST) -> dict | None:
    """The rule: the retailers in the order of the list, each to its cheapest local
    warehouse with room left for its orders. None if a retailer finds no warehouse
    with room."""
    room, warehouse = dict(capacity), {}
    for r in orders:
        fits = [l for l in capacity if room[l] >= orders[r] - TOL]
        if not fits:
            return None
        warehouse[r] = min(fits, key=lambda l: cost[l, r])
        room[warehouse[r]] -= orders[r]
    return _plan(warehouse, orders, capacity, cost)


def build_assignment(orders: dict = YEARLY_ORDERS, capacity: dict = NODE_CAPACITY_YEAR, cost: dict = COST,
                     split: bool = False):
    """The generalized assignment model, not solved; with ``split`` the transportation
    problem on the same data, whose variables are continuous between 0 and 1. Returns
    the model, its variables x by (l, r) and the cost expression."""
    model = pulp.LpProblem("generalized_assignment", pulp.LpMinimize)
    # x[l, r] = 1 if local warehouse l serves retailer r; with split, the share of
    # the orders of r that l serves
    x = {(l, r): (model.add_variable(f"x_{_key(l)}_{_key(r)}", lowBound=0, upBound=1) if split
                  else _binary(model, f"x_{_key(l)}_{_key(r)}")) for l in capacity for r in orders}
    total = pulp.lpSum(cost[l, r] * orders[r] * x[l, r] for l in capacity for r in orders)
    model += total
    for r in orders:
        # Each retailer is served by exactly one local warehouse (with split, its
        # shares add up to 1)
        model += (pulp.lpSum(x[l, r] for l in capacity) == 1, f"one_warehouse_{_key(r)}")
    for l in capacity:
        # Node capacity of each local warehouse for a year
        model += (pulp.lpSum(orders[r] * x[l, r] for r in orders) <= capacity[l], f"node_capacity_{_key(l)}")
    return model, x, total


def assignment_plan(orders: dict = YEARLY_ORDERS, capacity: dict = NODE_CAPACITY_YEAR, cost: dict = COST,
                    split: bool = False) -> dict | None:
    """Solve the generalized assignment model, or with ``split`` the transportation
    problem. Returns the cost (EUR/year), the share of the orders of each retailer
    that each local warehouse serves, by (l, r), the warehouse of each retailer that
    is served from one warehouse only, and the load of each warehouse (bikes/year).
    None if the model has no solution."""
    model, x, _ = build_assignment(orders, capacity, cost, split)
    if not _optimal(model.solve(_solver())):
        return None
    share = {key: (0.0 if abs(v.value()) < TOL else v.value()) for key, v in x.items()}
    warehouse = {r: l for (l, r), v in share.items() if v > 1 - TOL}
    return {"cost": pulp.value(model.objective), "share": share, "warehouse": warehouse,
            "load": {l: sum(orders[r] * share[l, r] for r in orders) for l in capacity}}


def only_assignment(orders: dict = YEARLY_ORDERS, capacity: dict = NODE_CAPACITY_YEAR, cost: dict = COST,
                    split: bool = False) -> bool | None:
    """True if the optimal plan of the generalized assignment (or, with ``split``, of
    the transportation problem) is the only one; None if the model has no solution."""
    model, x, total = build_assignment(orders, capacity, cost, split)
    if not _optimal(model.solve(_solver())):
        return None
    best = pulp.value(model.objective)
    if not split:
        chosen = [v for v in x.values() if v.value() > 0.5]
        return _only_selection(model, chosen, [v for v in x.values() if v.value() <= 0.5], best)
    # Continuous variables: with the cost fixed at its optimum, every share has the
    # same minimum and maximum
    model += (total <= best + 1e-6, "optimal_cost")
    for v in x.values():
        ends = []
        for sense in (pulp.LpMinimize, pulp.LpMaximize):
            model.sense = sense
            model.setObjective(v)
            model.solve(_solver())
            ends.append(v.value())
        if abs(ends[0] - ends[1]) > 1e-6:
            return False
    return True


# ---------------------------------------------------------------------------
# Which candidate sites act as regional warehouses: set covering
# ---------------------------------------------------------------------------

def reach(times: dict = TRAVEL_TIME, max_time: float = MAX_TRAVEL_TIME) -> dict:
    """The local warehouses within the maximum road travel time of each candidate
    site: the candidate set of the site."""
    return {n: [l for k, l in enumerate(LOCAL_EXP) if times[n][k] <= max_time + TOL] for n in times}


def build_covering(sets: dict, site_cost: dict = SITE_COST, exactly_one: bool = False):
    """The set covering model ("at least one") or, with ``exactly_one``, the same
    sets as a partition, not solved. Returns the model, its variables y by site and
    the cost expression."""
    model = pulp.LpProblem("set_covering", pulp.LpMinimize)
    # y[n] = 1 if candidate site n acts as a regional warehouse
    y = {n: _binary(model, f"y_{_key(n)}") for n in sets}
    total = pulp.lpSum(site_cost[n] * y[n] for n in sets)
    model += total
    for l in LOCAL_EXP:
        reached = pulp.lpSum(y[n] for n in sets if l in sets[n])
        model += ((reached == 1) if exactly_one else (reached >= 1), f"local_{_key(l)}")
    return model, y, total


def covering_plan(times: dict = TRAVEL_TIME, max_time: float = MAX_TRAVEL_TIME, site_cost: dict = SITE_COST,
                  exactly_one: bool = False) -> dict | None:
    """The regional warehouses of least cost. Returns the sites chosen, the cost
    (thousand EUR/year), the chosen sites that reach each local warehouse and the
    candidate set of every site; None if the model has no solution, also when a
    local warehouse is within reach of no site."""
    sets = reach(times, max_time)
    model, y, _ = build_covering(sets, site_cost, exactly_one)
    if not _optimal(model.solve(_solver())):
        return None
    chosen = [n for n in sets if y[n].value() > 0.5]
    return {"sites": chosen, "cost": pulp.value(model.objective), "sets": sets,
            "reached by": {l: [n for n in chosen if l in sets[n]] for l in LOCAL_EXP}}


def only_covering(times: dict = TRAVEL_TIME, max_time: float = MAX_TRAVEL_TIME, site_cost: dict = SITE_COST,
                  exactly_one: bool = False) -> bool | None:
    """True if the optimal choice of regional warehouses is the only one; None if
    the model has no solution."""
    model, y, _ = build_covering(reach(times, max_time), site_cost, exactly_one)
    if not _optimal(model.solve(_solver())):
        return None
    chosen = [v for v in y.values() if v.value() > 0.5]
    return _only_selection(model, chosen, [v for v in y.values() if v.value() <= 0.5], pulp.value(model.objective))


# ---------------------------------------------------------------------------
# The weekly routes of local warehouse 2: set partitioning
# ---------------------------------------------------------------------------

def candidate_routes(weekly: dict = WEEKLY_ORDERS, truck: float = TRUCK_CAPACITY, max_km: float = MAX_ROUTE_KM,
                     fixed: float = ROUTE_FIXED_COST, per_km: float = ROUTE_KM_COST, km: list = ROUTE_KM,
                     nodes: list = ROUTE_NODES, max_stops: int | None = None) -> list[dict]:
    """Every candidate route: it leaves the local warehouse, visits one or more of its
    retailers and returns, carries their weekly orders within the capacity of the
    small truck and drives at most the longest distance of a working day. Each route visits
    its retailers in the order of least distance, found by trying every order; of
    two orders with the same distance, the first one tried. Its cost is the fixed
    cost of a route plus the cost of its kilometres, rounded to the cent. With
    ``max_stops``, only the routes of at most that many retailers."""
    where = {node: k for k, node in enumerate(nodes)}
    retailers = [r for r in nodes[1:] if r in weekly]
    routes = []
    for size in range(1, (max_stops or len(retailers)) + 1):
        for group in itertools.combinations(retailers, size):
            load = sum(weekly[r] for r in group)
            if load > truck:
                continue
            best = None
            for order in itertools.permutations(group):
                stops = [nodes[0], *order, nodes[0]]
                distance = round(sum(km[where[a]][where[b]] for a, b in zip(stops, stops[1:])), 1)
                if best is None or distance < best[0]:
                    best = (distance, order)
            if best[0] <= max_km + TOL:
                routes.append({"stops": list(best[1]), "km": best[0], "load": load,
                               "cost": round(fixed + per_km * best[0], 2)})
    for k, route in enumerate(routes, 1):
        route["number"] = k
    return routes


def short_list(routes: list[dict], stops: int = SHORT_LIST_STOPS) -> list[dict]:
    """The routes of a list that visit at most ``stops`` retailers."""
    return [route for route in routes if len(route["stops"]) <= stops]


def build_routes(routes: list[dict], retailers: list = ROUTE_RETAILERS, exactly_one: bool = True):
    """The set partitioning model over a list of candidate routes or, with
    ``exactly_one`` False, the set covering model over the same list, not solved.
    Returns the model, its variables y by route number and the cost expression."""
    model = pulp.LpProblem("set_partitioning", pulp.LpMinimize)
    # y[j] = 1 if candidate route j is driven in the week
    y = {route["number"]: _binary(model, f"y_{route['number']}") for route in routes}
    total = pulp.lpSum(route["cost"] * y[route["number"]] for route in routes)
    model += total
    for r in retailers:
        visits = pulp.lpSum(y[route["number"]] for route in routes if r in route["stops"])
        model += ((visits == 1) if exactly_one else (visits >= 1), f"retailer_{_key(r)}")
    return model, y, total


def route_plan(routes: list[dict] | None = None, retailers: list = ROUTE_RETAILERS,
               exactly_one: bool = True) -> dict | None:
    """The weekly routes of least cost among a list of candidate routes (by default,
    the full list). Returns the routes chosen, the cost (EUR/week), the distance
    (km/week) and the number of routes that visit each retailer; None if the model
    has no solution."""
    routes = candidate_routes() if routes is None else routes
    model, y, _ = build_routes(routes, retailers, exactly_one)
    if not _optimal(model.solve(_solver())):
        return None
    chosen = [route for route in routes if y[route["number"]].value() > 0.5]
    return {"routes": chosen, "cost": pulp.value(model.objective), "km": sum(route["km"] for route in chosen),
            "visits": {r: sum(r in route["stops"] for route in chosen) for r in retailers}}


def only_routes(routes: list[dict] | None = None, retailers: list = ROUTE_RETAILERS,
                exactly_one: bool = True) -> bool | None:
    """True if the optimal choice of routes is the only one; None if the model has no
    solution."""
    routes = candidate_routes() if routes is None else routes
    model, y, _ = build_routes(routes, retailers, exactly_one)
    if not _optimal(model.solve(_solver())):
        return None
    chosen = [v for v in y.values() if v.value() > 0.5]
    return _only_selection(model, chosen, [v for v in y.values() if v.value() <= 0.5], pulp.value(model.objective))


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

SEVERAL = "With these data other plans have the same optimal cost."


def _lon_lat(node: str) -> tuple[float, float]:
    return PLACES_EXP[node][2], PLACES_EXP[node][1]


def _map(ax, title: str) -> None:
    ax.set_title(f"{title}; positions follow the map, not to scale", fontsize=10)
    ax.set_xlim(-9.5, 3.8)
    ax.set_ylim(35.9, 44.2)
    ax.set_aspect(1.25)
    ax.axis("off")


def show_data() -> None:
    """Tables 1 to 5 and 7 of expanded_network.md: the retailers with their yearly
    orders, the local warehouses with their node capacity, the transport cost of
    each pair, the candidate sites with their fixed cost, and the travel times."""
    _display(pd.DataFrame({r: {"Place": PLACES_EXP[r][0], "Orders (bikes/year)": YEARLY_ORDERS[r]}
                           for r in RETAILERS_EXP}).T.rename_axis("Retailer"))
    _display(pd.DataFrame({l: {"Place": PLACES_EXP[l][0], "Node capacity (bikes/year)": NODE_CAPACITY_YEAR[l]}
                           for l in LOCAL_EXP}).T.rename_axis("Local warehouse"))
    print(f"Orders of all the retailers: {_number(sum(YEARLY_ORDERS.values()))} bikes/year; capacity of all the "
          f"local warehouses: {_number(sum(NODE_CAPACITY_YEAR.values()))} bikes/year.")
    table = pd.DataFrame({PLACES_EXP[l][0]: {place(r): f"{COST[l, r]:.2f}".replace(".", ",") for r in RETAILERS_EXP}
                          for l in LOCAL_EXP})
    _display(table.rename_axis("Transport cost (€/bike)"))
    _display(pd.DataFrame({n: {"Fixed cost (thousand €/year)": SITE_COST[n]} for n in SITES}).T
             .rename_axis("Candidate site"))
    _display(pd.DataFrame({n: {PLACES_EXP[l][0]: f"{TRAVEL_TIME[n][k]:.2f}".replace(".", ",")
                               for k, l in enumerate(LOCAL_EXP)} for n in SITES}).T
             .rename_axis("Travel time (h)"))
    _display(pd.DataFrame({place(r): {"Weekly orders (bikes)": WEEKLY_ORDERS[r]} for r in ROUTE_RETAILERS}).T
             .rename_axis(f"Retailers of {place(ROUTE_WAREHOUSE)}"))


@_light
def _assignment_figure(model_plan: dict, cheapest: dict) -> None:
    """The retailers joined to the local warehouse that serves them in the model; in
    red the retailers that do not go to their cheapest warehouse."""
    fig, ax = plt.subplots(figsize=(8.5, 6.4))
    for r, l in model_plan["warehouse"].items():
        moved = l != cheapest["warehouse"][r]
        (x0, y0), (x1, y1) = _lon_lat(l), _lon_lat(r)
        ax.plot([x0, x1], [y0, y1], color=SHORT if moved else "0.6", lw=1.6 if moved else 0.8, zorder=1)
    for r in RETAILERS_EXP:
        ax.scatter(*_lon_lat(r), s=12 + YEARLY_ORDERS[r] / 25, color="tab:blue", zorder=2)
    for l in LOCAL_EXP:
        x, y = _lon_lat(l)
        ax.scatter(x, y, s=70, marker="s", color="black", zorder=3)
        ax.annotate(PLACES_EXP[l][0], (x, y), xytext=(5, 4), textcoords="offset points", fontsize=7)
    ax.scatter([], [], s=40, color="tab:blue", label="retailer (size: yearly orders)")
    ax.scatter([], [], s=50, marker="s", color="black", label="local warehouse")
    ax.plot([], [], color=SHORT, lw=1.6, label="not served by its cheapest local warehouse")
    ax.legend(fontsize=7, loc="lower right")
    _map(ax, "Local warehouse of each retailer in the generalized assignment")
    plt.show()


def _assignment_table(plans: dict, orders: dict) -> pd.DataFrame:
    rows = {}
    for r in orders:
        row = {"Orders (bikes/year)": orders[r]}
        for label, plan in plans.items():
            if plan is None:
                row[label] = "—"
            elif "share" in plan and r not in plan["warehouse"]:
                row[label] = "; ".join(f"{PLACES_EXP[l][0]} {_number(100 * plan['share'][l, r], 1)} %"
                                       for l in LOCAL_EXP if plan["share"][l, r] > TOL)
            else:
                row[label] = PLACES_EXP[plan["warehouse"][r]][0]
        rows[place(r)] = row
    return pd.DataFrame(rows).T.rename_axis("Retailer")


def assignment(warehouse: str = ROUTE_WAREHOUSE, capacity: float | None = None) -> dict:
    """The four plans of the assignment, with the node capacity of one local warehouse
    changed: each retailer at its cheapest warehouse, the rule, the generalized
    assignment and the transportation problem. Their costs, the warehouse of each
    retailer in each plan, the load of each warehouse and a map of the assignment."""
    if warehouse not in LOCAL_EXP:
        raise ValueError(f"The local warehouse must be one of {', '.join(LOCAL_EXP)}.")
    capacities = dict(NODE_CAPACITY_YEAR)
    if capacity is not None:
        capacities[warehouse] = capacity
    print(f"Node capacity of {place(warehouse)}: {_number(capacities[warehouse])} bikes/year; capacity of all the "
          f"local warehouses: {_number(sum(capacities.values()))} bikes/year for "
          f"{_number(sum(YEARLY_ORDERS.values()))} bikes/year of orders.")
    plans = {"Cheapest": cheapest_plan(capacity=capacities), "Rule": rule_plan(capacity=capacities),
             "Generalized assignment": assignment_plan(capacity=capacities),
             "Transportation problem": assignment_plan(capacity=capacities, split=True)}
    cheapest, model_plan = plans["Cheapest"], plans["Generalized assignment"]
    over = ", ".join(f"{place(l)} ({_number(cheapest['load'][l])} for {_number(capacities[l])})"
                     for l in cheapest["over"])
    print(f"Each retailer at its cheapest local warehouse: {_number(cheapest['cost'], 2)} €/year; "
          + (f"not valid, the load exceeds the capacity of {over}." if over else "valid: no capacity is exceeded."))
    rule = plans["Rule"]
    print("The rule, in the order of the list: " + ("no valid plan: a retailer finds no local warehouse with room."
                                                    if rule is None else f"{_number(rule['cost'], 2)} €/year."))
    if model_plan is None:
        print("Generalized assignment: the model has no solution.")
        return plans
    moved = [r for r in RETAILERS_EXP if model_plan["warehouse"][r] != cheapest["warehouse"][r]]
    print(f"Generalized assignment: {_number(model_plan['cost'], 2)} €/year; {len(moved)} retailers do not go to "
          f"their cheapest local warehouse.")
    if not only_assignment(capacity=capacities):
        print(SEVERAL)
    if rule is not None:
        print(f"The rule costs {_number(100 * (rule['cost'] / model_plan['cost'] - 1), 1)} % more than the "
              f"generalized assignment.")
    split = plans["Transportation problem"]
    shared = [r for r in RETAILERS_EXP if r not in split["warehouse"]]
    print(f"Transportation problem: {_number(split['cost'], 2)} €/year, "
          f"{_number(100 * (1 - split['cost'] / model_plan['cost']), 1)} % less than the generalized assignment; "
          f"{len(shared)} retailers are split between two or more local warehouses.")
    changed = [r for r in RETAILERS_EXP if r in moved or r in shared
               or (rule is not None and rule["warehouse"][r] != cheapest["warehouse"][r])]
    print("Retailers that are not at their cheapest local warehouse in some plan:")
    _display(_assignment_table(plans, {r: YEARLY_ORDERS[r] for r in changed}))
    loads = pd.DataFrame({place(l): {"Node capacity": capacities[l],
                                     **{label: (plan["load"][l] if plan else "—") for label, plan in plans.items()}}
                          for l in LOCAL_EXP}).T
    _display(loads.round(1).rename_axis("Load of each local warehouse (bikes/year)"))
    _assignment_figure(model_plan, cheapest)
    return plans


@_light
def _covering_figure(plan: dict) -> None:
    """The candidate sites, the chosen ones in green, joined to the local warehouses
    within their reach."""
    fig, ax = plt.subplots(figsize=(8.5, 6.4))
    for n in plan["sites"]:
        for l in plan["sets"][n]:
            (x0, y0), (x1, y1) = _lon_lat(n), _lon_lat(l)
            ax.plot([x0, x1], [y0, y1], color="tab:green", lw=1, zorder=1)
    for l in LOCAL_EXP:
        x, y = _lon_lat(l)
        ax.scatter(x, y, s=55, marker="s", color=SHORT if len(plan["reached by"][l]) > 1 else "black", zorder=3)
        ax.annotate(PLACES_EXP[l][0], (x, y), xytext=(5, -9), textcoords="offset points", fontsize=7)
    for n in SITES:
        x, y = _lon_lat(n)
        ax.scatter(x, y, s=140, marker="^", color="tab:green" if n in plan["sites"] else "white",
                   edgecolors="tab:green", zorder=4)
        ax.annotate(n, (x, y), xytext=(6, 5), textcoords="offset points", fontsize=7, color="tab:green")
    ax.scatter([], [], s=80, marker="^", color="tab:green", label="candidate site chosen")
    ax.scatter([], [], s=80, marker="^", color="white", edgecolors="tab:green", label="candidate site not chosen")
    ax.scatter([], [], s=40, marker="s", color="black", label="local warehouse")
    ax.scatter([], [], s=40, marker="s", color=SHORT, label="within reach of two or more chosen sites")
    ax.legend(fontsize=7, loc="lower right")
    _map(ax, "Regional warehouses and the local warehouses within their reach")
    plt.show()


def covering(max_time: float = MAX_TRAVEL_TIME, exactly_one: bool = False) -> dict | None:
    """The candidate set of each site for a maximum travel time, and the regional
    warehouses of least cost with "at least one" (set covering) or "exactly one"."""
    plan = covering_plan(max_time=max_time, exactly_one=exactly_one)
    sets = reach(max_time=max_time)
    _display(pd.DataFrame({n: {"Fixed cost (thousand €/year)": SITE_COST[n],
                               "Local warehouses within reach": "; ".join(PLACES_EXP[l][0] for l in sets[n]) or "—"}
                           for n in SITES}).T.rename_axis(f"Candidate site, {_number(max_time, 2)} h"))
    form = "exactly one chosen site" if exactly_one else "at least one chosen site"
    unreached = [l for l in LOCAL_EXP if not any(l in s for s in sets.values())]
    if plan is None:
        print(f"Each local warehouse within reach of {form}: the model has no solution."
              + (f" Within reach of no candidate site: {', '.join(place(l) for l in unreached)}." if unreached
                 else ""))
        return None
    print(f"Each local warehouse within reach of {form}: regional warehouses at {', '.join(plan['sites'])}; "
          f"cost {_number(plan['cost'])} thousand €/year.")
    if not only_covering(max_time=max_time, exactly_one=exactly_one):
        print(SEVERAL)
    twice = {place(l): "; ".join(sites) for l, sites in plan["reached by"].items() if len(sites) > 1}
    if twice:
        print("Local warehouses within reach of two or more chosen sites:")
        _display(pd.DataFrame({"Chosen sites": twice}).rename_axis("Local warehouse"))
    _covering_figure(plan)
    return plan


def _route_name(route: dict) -> str:
    """The retailers of a route in the order of visits; the route leaves local
    warehouse 2 and returns to it."""
    return ", ".join(PLACES_EXP[r][0] for r in route["stops"])


def _route_table(routes: list[dict]) -> pd.DataFrame:
    return pd.DataFrame({route["number"]: {"Retailers, in the order of visits": _route_name(route), "Load (bikes)": route["load"],
                                           "Distance (km)": f"{route['km']:.1f}".replace(".", ","),
                                           "Cost (€)": f"{route['cost']:.2f}".replace(".", ",")}
                         for route in routes}).T.rename_axis("Candidate route")


@_light
def _routes_figure(plan: dict) -> None:
    """The routes chosen, each in its colour, from local warehouse 2 to its retailers."""
    fig, ax = plt.subplots(figsize=(7, 4.6))
    colours = plt.get_cmap("tab10")
    for k, route in enumerate(plan["routes"]):
        stops = [ROUTE_WAREHOUSE, *route["stops"], ROUTE_WAREHOUSE]
        xs, ys = zip(*(_lon_lat(node) for node in stops))
        ax.plot(xs, ys, color=colours(k), lw=1.8, label=f"Route {route['number']}", marker="o", ms=4)
    for r in ROUTE_RETAILERS:
        x, y = _lon_lat(r)
        ax.annotate(f"{PLACES_EXP[r][0]} ({WEEKLY_ORDERS[r]})", (x, y), xytext=(5, 5), textcoords="offset points",
                    fontsize=7)
    x, y = _lon_lat(ROUTE_WAREHOUSE)
    ax.scatter(x, y, s=80, marker="s", color="black", zorder=3)
    ax.legend(fontsize=7, loc="lower left")
    ax.set_title("Routes chosen; in brackets, the weekly orders (bikes); straight lines, not the roads", fontsize=10)
    ax.set_xlim(-1.3, 3.2)
    ax.set_ylim(40.9, 42.4)
    ax.set_aspect(1.25)
    ax.axis("off")
    plt.show()


def routes(truck: float = TRUCK_CAPACITY, full_list: bool = True) -> dict | None:
    """The candidate routes for a truck capacity, from the full list or from the short
    list, and the weekly routes of least cost with "exactly one" (set partitioning)
    and with "at least one" (set covering)."""
    candidates = candidate_routes(truck=truck)
    if not full_list:
        candidates = short_list(candidates)
    which = "full list" if full_list else f"short list (routes of at most {SHORT_LIST_STOPS} retailers)"
    print(f"Truck capacity {_number(truck)} bikes; longest route {_number(MAX_ROUTE_KM)} km; cost of a route "
          f"{_number(ROUTE_FIXED_COST)} € plus {_number(ROUTE_KM_COST, 2)} €/km. {which.capitalize()}: "
          f"{len(candidates)} candidate routes.")
    _display(_route_table(candidates))
    plan = route_plan(candidates)
    if plan is None:
        print("Set partitioning (each retailer on exactly one route): the model has no solution.")
        too_big = [place(r) for r in ROUTE_RETAILERS if WEEKLY_ORDERS[r] > truck]
        if too_big:
            print(f"Weekly orders larger than the truck, on no candidate route: {', '.join(too_big)}.")
        return None
    print(f"Set partitioning (each retailer on exactly one route): routes "
          f"{', '.join(str(route['number']) for route in plan['routes'])}; {_number(plan['cost'], 2)} €/week, "
          f"{_number(plan['km'], 1)} km.")
    if not only_routes(candidates):
        print(SEVERAL)
    _display(_route_table(plan["routes"]).rename_axis("Route chosen"))
    cover = route_plan(candidates, exactly_one=False)
    twice = [place(r) for r, n in cover["visits"].items() if n > 1]
    same = sorted(route["number"] for route in cover["routes"]) == sorted(route["number"] for route in plan["routes"])
    print(f"Set covering (each retailer on at least one route): {_number(cover['cost'], 2)} €/week; "
          + ("the same routes." if same else f"routes {', '.join(str(route['number']) for route in cover['routes'])}"
             + (f"; on two or more routes: {', '.join(twice)}." if twice else ".")))
    _routes_figure(plan)
    return plan
