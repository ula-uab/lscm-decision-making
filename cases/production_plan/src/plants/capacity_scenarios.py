"""M4B · Master Planning for Electric Bicycles: Optimization Model and Scenario Analysis (capacity_scenarios.md): the model of retailers.md (M4)
with a price that can change by month, two capacity options, each one with its
cost, and plant 3 open or closed. M4 does not change: M4B is a version of its own, built on it.

What M4B adds to M4:

1. a demand growth by month: the orders of the retailers are their share of a
   base forecast raised by the growth of their month;
2. a price by month, with the discount of a price promotion in the months in
   which it applies; the lost-sale cost of a month is its price;
3. overtime at a plant, which relaxes its assembly capacity;
4. rented storage next to the central warehouse, which relaxes its storage
   capacity;
5. plant 3 open or closed for the whole horizon, with its fixed cost: a datum,
   open or closed, or a binary variable.

The model reuses the list of arcs and the functions ``entering`` and ``leaving``
of M3, the data of M4 and the check of a single optimal plan of M2. Written with
PuLP and solved with HiGHS.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import pulp

from .central_warehouse import SEVERAL, only_optimal
from .data import (ARCS_M4, BACKORDER_SHARE, BASE_FORECAST, CENTRAL, F, K, K_h_node_m4, K_n, LOCAL, NODES_M4,
                   PLACES_M4, PRICE, REGIONAL, RETAILERS, SHARE_M4, T, b_0, c, c_F, c_b, c_h_node_m4, c_o,
                   c_u, h_node_0_m4, h_node_end_m4, o_max, u_max)
from .distribution_network import entering, leaving
from .model import TOL, _optimal
from .show import COLOURS, SHORT, _display, _european_axes, _light, _number

PLANT_3 = "Plant 3"
OPEN, CLOSED, VARIABLE = "open", "closed", "variable"     # plant 3: a datum, open or closed, or a binary variable
STAGES = {"Plants": F, "Central warehouse": [CENTRAL], "Regional warehouses": REGIONAL,
          "Local warehouses": LOCAL}
NO_OVERTIME = {f: 0 for f in F}
NO_FIXED_COST = {f: 0 for f in F}


def _key(node: str) -> str:
    return node.replace(" ", "")


def _by_month(value: float | dict, months=T) -> dict:
    """A datum given as one number for every month, or by month, read by month."""
    return dict(value) if isinstance(value, dict) else {t: value for t in months}


def orders(demand: dict = BASE_FORECAST, growth: float | dict = 0.0, share: dict = SHARE_M4, months=T) -> dict:
    """The orders of each retailer in each month (bikes): its share of the base
    forecast of the month raised by the demand growth of that month. ``growth`` is
    one number for every month (0,10 for 10 %) or a growth by month."""
    rise = _by_month(growth, months)
    return {(r, t): share[r] * demand[t] * (1 + rise[t]) for r in share for t in months}


def promotion(months_of_the_promotion, discount: float = 0.0, growth: float = 0.0,
              price: dict = PRICE, months=T) -> dict:
    """The price and the demand growth of each month under a price promotion, as the
    arguments ``price`` and ``growth`` of ``build`` and ``solve``: in the months of
    the promotion the price falls by the discount and the orders grow by ``growth``;
    the other months keep the price and the orders of the base forecast."""
    chosen = {months_of_the_promotion} if isinstance(months_of_the_promotion, str) else set(months_of_the_promotion)
    if not chosen <= set(months):
        raise ValueError(f"The months of the promotion must be among {', '.join(months)}.")
    return {"price": {t: price[t] * (1 - discount) if t in chosen else price[t] for t in months},
            "growth": {t: growth if t in chosen else 0.0 for t in months}}


def build(order: dict | None = None, demand: dict = BASE_FORECAST, growth: float | dict = 0.0,
          price: float | dict = PRICE, plant_3: str = OPEN, overtime: dict | None = None,
          overtime_cost: float = c_o, rented: float = 0.0, rented_cost: float = c_u,
          fixed_cost: dict | None = None,
          months=T, arc_list: list = ARCS_M4, backorder_share: dict = BACKORDER_SHARE,
          holding: dict = c_h_node_m4, storage: dict = K_h_node_m4,
          node_capacity: dict = K_n, initial: dict = h_node_0_m4, final: dict | None = h_node_end_m4,
          backorder_cost: float = c_b, backorders_initial: float = b_0, capacity: dict = K, nodes=NODES_M4,
          plants=F, retailers=RETAILERS, warehouse: str = CENTRAL):
    """The model of M4B, not solved. ``order`` gives the orders of each retailer in
    each month, by (r, t); by default, its share of the base forecast with the
    demand growth given. ``price`` is the price of a bike, one number for every
    month or by month, and it is also the lost-sale cost of its month.
    ``plant_3`` is "open" or "closed", a datum, or "variable", a binary variable;
    ``overtime`` gives the maximum overtime of each plant (bikes/month),
    ``rented`` the bikes that can be rented next to the central warehouse, and
    ``fixed_cost`` the fixed cost of each plant (EUR/month). Without them there
    is no overtime, no rented storage and no fixed cost: with the data of M4 the
    model is then M4.

    Returns the model, a dict of its variables by kind ("p" by (f, t); "o" by
    (f, t); "x" by (a, t); "h" by (i, t); "u" by t; "s", "b", "l" by (r, t)) and
    the cost expression."""
    if plant_3 not in (OPEN, CLOSED, VARIABLE):
        raise ValueError(f'Plant 3 must be "{OPEN}", "{CLOSED}" or "{VARIABLE}".')
    order = order or orders(demand=demand, growth=growth, months=months)
    price = _by_month(price, months)
    overtime = NO_OVERTIME if overtime is None else overtime
    fixed_cost = NO_FIXED_COST if fixed_cost is None else fixed_cost
    model = pulp.LpProblem("capacity_scenarios", pulp.LpMinimize)
    # p = bikes assembled, o = of them, assembled in overtime; x = bikes shipped
    # on each arc; h = stock at the end of the month, u = of it, in rented
    # storage; s = deliveries, b = backorders at the end of the month and
    # l = lost sales of each retailer
    p = {(f, t): model.add_variable(f"p_{_key(f)}_{t}", lowBound=0) for f in plants for t in months}
    o = {(f, t): model.add_variable(f"o_{_key(f)}_{t}", lowBound=0) for f in plants for t in months}
    x = {(a, t): model.add_variable(f"x_{a}_{t}", lowBound=0) for a in range(len(arc_list)) for t in months}
    h = {(i, t): model.add_variable(f"h_{_key(i)}_{t}", lowBound=0) for i in nodes for t in months}
    u = {t: model.add_variable(f"u_{t}", lowBound=0) for t in months}
    s = {(r, t): model.add_variable(f"s_{_key(r)}_{t}", lowBound=0) for r in retailers for t in months}
    b = {(r, t): model.add_variable(f"b_{_key(r)}_{t}", lowBound=0) for r in retailers for t in months}
    l = {(r, t): model.add_variable(f"l_{_key(r)}_{t}", lowBound=0) for r in retailers for t in months}
    variables = {"p": p, "o": o, "x": x, "h": h, "u": u, "s": s, "b": b, "l": l}
    # delta[f] = 1 if plant f is open from January to June. Plants 1 and 2 are
    # always open; plant 3 is open, closed, or a binary variable
    delta = {f: 1 for f in plants}
    if plant_3 == CLOSED:
        delta[PLANT_3] = 0
    elif plant_3 == VARIABLE:
        delta[PLANT_3] = model.add_variable(f"delta_{_key(PLANT_3)}", cat="Binary")
        variables["d"] = {PLANT_3: delta[PLANT_3]}
    # Minimise the assembly, overtime, holding, rented storage, transport,
    # backorder and lost-sale cost, plus the fixed cost of the plants that are open
    cost = (pulp.lpSum(c[f] * p[f, t] + overtime_cost * o[f, t] for f in plants for t in months)
            + pulp.lpSum(holding[i] * h[i, t] for i in nodes for t in months)
            + pulp.lpSum(rented_cost * u[t] for t in months)
            + pulp.lpSum(arc_list[a]["cost"] * x[a, t] for a in range(len(arc_list)) for t in months)
            + pulp.lpSum(backorder_cost * b[r, t] + price[t] * l[r, t] for r in retailers for t in months)
            + pulp.lpSum(len(months) * fixed_cost[f] * delta[f] for f in plants))
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
            # Storage capacity, relaxed at the central warehouse by the rented storage
            rent = u[t] if i == warehouse else 0
            model += (h[i, t] - rent <= storage[i], f"storage_{_key(i)}_{t}")
            if i in node_capacity:
                model += (arriving <= node_capacity[i], f"node_capacity_{_key(i)}_{t}")
        if final is not None:
            model += (h[i, months[-1]] >= final[i], f"final_stock_{_key(i)}")
    for t in months:
        # Rented storage: the bikes rented next to the central warehouse
        model += (u[t] <= rented, f"rented_storage_{t}")
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
            # Assembly capacity, relaxed by the overtime; a closed plant assembles nothing
            model += (p[f, t] - o[f, t] <= capacity[f][t] * delta[f], f"capacity_{_key(f)}_{t}")
            # Overtime at an open plant
            model += (o[f, t] <= overtime[f] * delta[f], f"overtime_{_key(f)}_{t}")
    return model, variables, cost


def only_plan(**data) -> bool | None:
    """True if the optimal plan of M4B with the data given (the arguments of
    ``build``) is the only one; False if several plans have the optimal cost; None
    if the model has no solution. With plant 3 as a binary variable, the check is
    made with the plant fixed at the value of the optimal plan."""
    if data.get("plant_3") == VARIABLE:
        solution = solve(**data)
        if solution is None:
            return None
        data = {**data, "plant_3": OPEN if solution["open"][PLANT_3] else CLOSED}
    model, var, cost = build(**data)
    return only_optimal(model, [v for group in var.values() for v in group.values()], cost)


def _stage_stock(stock: dict, months: list) -> dict:
    """The seasonal stock at the end of each month, by stage and in total (bikes)."""
    rows = {name: {t: sum(stock[i, t] for i in group) for t in months} for name, group in STAGES.items()}
    rows["Total"] = {t: sum(rows[name][t] for name in STAGES) for t in months}
    return rows


def solve(**data) -> dict | None:
    """Solve M4B with the data given (the arguments of ``build``). Returns the cost
    and the margin of the plan (EUR); the price of each month (EUR/bike); the bikes
    assembled at each plant, of them in overtime, shipped on each arc, in stock at
    each node and in rented storage; the deliveries, backorders and lost sales of
    each retailer, by month (bikes); which plants are open; the capacity
    utilization of each plant in the horizon; the lost sales of each retailer, as a
    share of its orders; and the seasonal stock by stage. None if the model has no
    solution."""
    model, var, _ = build(**data)
    if not _optimal(model.solve(pulp.HiGHS(msg=False))):
        return None
    months = sorted({t for _, t in var["p"]}, key=T.index)
    plants = data.get("plants", F)
    retailers = data.get("retailers", RETAILERS)
    capacity = data.get("capacity", K)
    price = _by_month(data.get("price", PRICE), months)
    order = data.get("order") or orders(demand=data.get("demand", BASE_FORECAST),
                                        growth=data.get("growth", 0.0), months=months)
    clean = lambda v: 0.0 if abs(v) < TOL else v      # noqa: E731  (no "-0.0" in tables)
    values = {kind: {key: clean(v.value()) for key, v in var[kind].items()} for kind in var}
    delta = {f: 1.0 for f in plants}
    if data.get("plant_3") == CLOSED:
        delta[PLANT_3] = 0.0
    elif data.get("plant_3") == VARIABLE:
        delta[PLANT_3] = round(values["d"][PLANT_3])
    cost = pulp.value(model.objective)
    return {
        "months": months, "arcs": data.get("arc_list", ARCS_M4), "orders": order, "price": price,
        "cost": cost,
        # The lost-sale cost of a month is its price, so the price of the bikes
        # delivered less the cost of the plan is the orders at that price less the cost
        "margin": sum(price[t] * order[r, t] for r in retailers for t in months) - cost,
        "assembly": values["p"], "overtime": values["o"], "flow": values["x"], "stock": values["h"],
        "rented": values["u"],
        "deliveries": values["s"], "backorders": values["b"], "lost sales": values["l"],
        "open": delta,
        "capacity utilization": {f: sum(values["p"][f, t] for t in months) / sum(capacity[f][t] for t in months)
                                 for f in plants},
        "lost sales share": {r: (sum(values["l"][r, t] for t in months) / sum(order[r, t] for t in months)
                                 if sum(order[r, t] for t in months) else 0.0) for r in retailers},
        "seasonal stock": _stage_stock(values["h"], months),
    }


# ---------------------------------------------------------------------------
# What the notebook shows
# ---------------------------------------------------------------------------

def chosen_months(*flags: bool, months=T) -> list:
    """The months chosen with one flag per month, in the order of the horizon: the
    months of a price promotion."""
    return [t for t, on in zip(months, flags) if on]


def show_data() -> None:
    """Tables 1 and 2 of capacity_scenarios.md: the base forecast with the orders of
    each retailer and the price of each month, and the capacity options with the
    fixed cost of plant 3."""
    order = orders()
    table = pd.DataFrame({f"{r} ({PLACES_M4[r][0]})": {t: order[r, t] for t in T} for r in RETAILERS}).T
    table.insert(0, "Share", [f"{_number(100 * SHARE_M4[r])} %" for r in RETAILERS])
    table.loc["Base forecast"] = ["100 %"] + [BASE_FORECAST[t] for t in T]
    table.loc["Price (€/bike)"] = [""] + [PRICE[t] for t in T]
    print("Base forecast, share and orders of each retailer (bikes/month), and price (€/bike)")
    _display(table)
    options = {f"Overtime limit at {f.lower()}": f"{_number(o_max[f])} bikes/month" for f in F}
    options["Overtime cost (over the unit assembly cost)"] = f"{_number(c_o)} €/bike"
    options["Rented storage limit, next to central warehouse"] = f"{_number(u_max)} bikes"
    options["Rented storage cost (over warehouse holding cost)"] = f"{_number(c_u)} €/(bike·month)"
    options["Fixed cost of plant 3 open"] = f"{_number(c_F[PLANT_3])} €/month"
    print("Capacity options and fixed cost of plant 3")
    _display(pd.DataFrame({"Value": options}))


def _scenario(growth: float = 0.0, promotion_months=(), discount: float = 0.0,
              promotion_growth: float = 0.0) -> dict:
    """The price and the demand growth of each month, from the percentages of the
    form: a growth in every month and a price promotion in the months chosen."""
    rise = {t: growth / 100 for t in T}
    price = dict(PRICE)
    for t in promotion_months:
        rise[t] = promotion_growth / 100
        price[t] = PRICE[t] * (1 - discount / 100)
    return {"growth": rise, "price": price}


def _options(plant_3: str = OPEN, overtime: bool = False, overtime_cost: float = c_o,
             rented_storage: bool = False, rented_cost: float = c_u, fixed_cost: float = 0.0) -> dict:
    """The options of the plan, from the values of the form."""
    return {"plant_3": plant_3,
            "overtime": o_max if overtime else NO_OVERTIME, "overtime_cost": overtime_cost,
            "rented": u_max if rented_storage else 0.0, "rented_cost": rented_cost,
            "fixed_cost": {**NO_FIXED_COST, PLANT_3: fixed_cost}}


def _price_and_orders(solution: dict) -> None:
    """The price of each month and the orders of the six retailers, under the
    scenario solved."""
    months, order = solution["months"], solution["orders"]
    print("Price and orders of each month in the scenario")
    _display(pd.DataFrame({t: {"Price (€/bike)": solution["price"][t],
                               "Orders of the six retailers (bikes/month)": sum(order[r, t] for r in RETAILERS)}
                           for t in months}))


def _plant_tables(solution: dict) -> None:
    """The bikes assembled at each plant, of them in overtime, and the seasonal stock
    at the end of each month by stage, with the rented storage."""
    months = solution["months"]
    rows = {}
    for f in F:
        rows[f] = {t: solution["assembly"][f, t] for t in months}
        if o_max[f] > 0:
            rows[f"{f}, in overtime"] = {t: solution["overtime"][f, t] for t in months}
    print("Bikes assembled (bikes/month); each row «in overtime» is part of the row of its plant")
    _display(pd.DataFrame(rows).T)
    stock = {}
    for name, row in solution["seasonal stock"].items():
        stock[name] = dict(row)
        if name == "Central warehouse":
            stock["Central warehouse, in rented storage"] = {t: solution["rented"][t] for t in months}
    print("Stock at the end of the month at each stage (bikes); the row «in rented storage» is part of the central "
          "warehouse and of the total")
    _display(pd.DataFrame(stock).T)


def _lost_sales_table(solution: dict) -> None:
    """The lost sales of each retailer in each month, and in the horizon as a share
    of its orders, with its backorder share, and the backorders at the end of each
    month. Nothing if the plan delivers every order."""
    months = solution["months"]
    losing = [r for r in RETAILERS if any(solution["lost sales"][r, t] > TOL for t in months)]
    if not losing:
        return
    table = pd.DataFrame({f"{r} ({PLACES_M4[r][0]})": {t: solution["lost sales"][r, t] for t in months}
                          for r in losing}).T
    table.insert(0, "Share of its orders",
                 [f"{_number(100 * solution['lost sales share'][r], 1)} %" for r in losing])
    table.insert(1, "Backorder share", [_number(BACKORDER_SHARE[r], 1) for r in losing])
    print("Lost sales (bikes)")
    _display(table)
    waiting = [r for r in RETAILERS if any(solution["backorders"][r, t] > TOL for t in months)]
    if waiting:
        print("Backorders at the end of the month (bikes)")
        _display(pd.DataFrame({f"{r} ({PLACES_M4[r][0]})": {t: solution["backorders"][r, t] for t in months}
                               for r in waiting}).T)


@_light
def _figure(solution: dict) -> None:
    """Left: the capacity utilization of each plant in each month, with the share of
    the capacity that the overtime adds above 100 %. Right: the lost sales of each
    retailer in each month."""
    months = solution["months"]
    capacity = K
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 4.6))
    width = 0.26
    for k, f in enumerate(F):
        values = [100 * solution["assembly"][f, t] / capacity[f][t] for t in months]
        places = [i + (k - 1) * width for i in range(len(months))]
        left.bar(places, values, width=width, color=COLOURS[f], label=f)
    left.axhline(100, color=SHORT, lw=1, ls="--")
    left.annotate("assembly capacity; above it, overtime", (len(months) - 0.5, 100), xytext=(0, 3), textcoords="offset points",
                  fontsize=7, color=SHORT, ha="right")
    left.set_xticks(range(len(months)), months)
    left.set_ylabel("Capacity utilization (% of the assembly capacity)")
    left.set_ylim(0, 125)
    left.set_title("Capacity utilization of each plant in each month", fontsize=10)
    left.legend(fontsize=7, loc="upper left")
    left.spines[["top", "right"]].set_visible(False)

    bottom = [0.0] * len(months)
    colours = plt.get_cmap("tab10")
    for k, r in enumerate(RETAILERS):
        values = [solution["lost sales"][r, t] for t in months]
        right.bar(range(len(months)), values, bottom=bottom, color=colours(k), width=0.7,
                  label=f"{r} ({PLACES_M4[r][0]})")
        bottom = [b + v for b, v in zip(bottom, values)]
    right.set_xticks(range(len(months)), months)
    right.set_ylabel("Lost sales (bikes)")
    right.set_ylim(0, max(10, max(bottom) * 1.25))
    if max(bottom) <= TOL:
        right.text(0.5, 0.5, "no lost sales", transform=right.transAxes, ha="center", va="center",
                   fontsize=9, color=SHORT)
    right.set_title("Lost sales of each retailer", fontsize=10)
    right.legend(fontsize=7, loc="upper left")
    right.spines[["top", "right"]].set_visible(False)
    _european_axes(fig)
    plt.show()


def plan(growth: float = 0.0, promotion_months=(), discount: float = 0.0, promotion_growth: float = 0.0,
         plant_3: str = OPEN, overtime: bool = False, overtime_cost: float = c_o,
         rented_storage: bool = False, rented_cost: float = c_u, fixed_cost: float = 0.0) -> dict | None:
    """The plan of a scenario, with the values of the form of the notebook. The
    percentages are given as percentages, not as shares: ``growth`` is the demand
    growth of every month, and ``promotion_months``, ``discount`` and
    ``promotion_growth`` are the months of a price promotion, its discount and the
    growth of the orders of those months. ``plant_3`` is "open", "closed" or
    "variable"; ``overtime`` and ``rented_storage`` say whether each option is
    available, with its cost; ``fixed_cost`` is the fixed cost of plant 3
    (EUR/month).

    Shows the cost and the margin of the plan, the margin under the base forecast
    with the same options, the capacity utilization of each plant, the bikes
    assembled, the seasonal stock, the lost sales and the figure."""
    options = _options(plant_3, overtime, overtime_cost, rented_storage, rented_cost, fixed_cost)
    data = {**_scenario(growth, promotion_months, discount, promotion_growth), **options}
    solution = solve(**data)
    if solution is None:
        print("The model has no solution with these values.")
        return None
    base = solve(**options)
    is_open = solution["open"][PLANT_3] == 1
    state = {OPEN: "open", CLOSED: "closed"}.get(plant_3, f"a binary variable, {'open' if is_open else 'closed'} "
                                                          "in the optimal plan")
    fixed = len(T) * fixed_cost if is_open else 0
    print(f"Plant 3: {state}, with a fixed cost of {_number(fixed_cost)} €/month (value of the form). "
          f"Overtime: {'yes' if overtime else 'no'}. "
          f"Rented storage: {'up to ' + _number(u_max) + ' bikes' if rented_storage else 'no'}.")
    print(f"Plan of the scenario: cost {_number(solution['cost'], 2)} €, of which {_number(fixed)} € is the fixed cost "
          f"of plant 3; margin {_number(solution['margin'], 2)} €; "
          f"lost sales {_number(sum(solution['lost sales'].values()))} bikes.")
    again = " (decided again for the base forecast)" if plant_3 == VARIABLE else ""
    print(f"Margin under the base forecast (demand growth 0, no promotion), with the same setting of plant 3{again}, "
          f"the same fixed cost and the same capacity options, to compare with the margin of the scenario: "
          f"{_number(base['margin'], 2)} €.")
    print(SEVERAL if not only_plan(**data) else "No other plan has the same optimal cost: the tables below are those of the only optimal plan.")
    print("Capacity utilization in the six months (bikes assembled, overtime included, as a share of the assembly "
          "capacity of the six months): "
          + "; ".join(f"{f} {_number(100 * solution['capacity utilization'][f], 1)} %" for f in F) + ".")
    _price_and_orders(solution)
    _plant_tables(solution)
    _lost_sales_table(solution)
    _figure(solution)
    return solution
