"""Figures that several notebooks of the case share, so that they all look the same:

- ``network``: the network of M3 or M4 by stages, with the geometry of figure
  CS-F1 of the statement, the data or the plan of each node under its label and
  of each arc on the arc;
- ``places_map``: the places of a network on the outline of the Iberian
  Peninsula, one symbol for each kind of element and the city as the only label;
- the panels of a plan by month: the assembly of each plant against its capacity,
  the stock at each stage of the network, bars stacked by month with the numbers
  inside, and the shadow prices of the full capacities of one month.

The style is that of the master plan of lot_sizing: the colours of the plants of
``show.COLOURS``, the numbers inside the bars and the capacity as a dashed line.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Polygon, Rectangle

from .data import (ARCS_M4, BACKORDER_SHARE, CENTRAL, RAIL_TERMINAL, RETAILERS, F, K, K_h, K_h_node_m4, K_n, T, c, c_h,
                   c_h_node_m4, c_l, h_node_0_m4, h_node_end_m4)
from .show import COLOURS, SHORT, _light, _number

# The geometry of the figure of the network of M4 in the statement (figure CS-F1):
# the position, shape and label of each node and the route of each arc. It is
# written by web/T3.Planning/lot_sizing/dump_geometry.py of the lecturer repository;
# copy it again here when that figure changes
NETWORK_FIGURE = Path(__file__).with_name("network_m4.json")
INK, TEXT, FILL = "#034854", "#444444", "#F2F6F6"
IDLE = "0.78"                     # an arc with no flow

# Outline of Spain, Portugal, France and Andorra: Natural Earth, 1:50m Cultural
# Vectors, Admin 0 - Countries, version 5.1.1 (public domain, naturalearthdata.com;
# geojson/ne_50m_admin_0_countries.geojson of github.com/nvkelso/natural-earth-vector),
# cut to the window of the peninsula, longitude -10 to 4,6 and latitude 35,8 to 44,1
PENINSULA = Path(__file__).with_name("peninsula.json")
SEA, SPAIN, NEIGHBOUR = "#DCEBF5", "#D4D4D4", "#ECECEC"

# One symbol and one colour for each kind of element of a network on the map
KINDS = {
    "Plant": dict(marker="s", color="tab:blue", s=55),
    "Central warehouse": dict(marker="v", color="dimgray", s=75),
    "Rail terminal": dict(marker="o", color="black", s=30),
    "Regional warehouse": dict(marker="v", color="tab:olive", s=75),
    "Local warehouse": dict(marker="v", color="tab:cyan", s=60),
    "Retailer": dict(marker="D", color="tab:red", s=32),
    "Candidate site for a regional warehouse": dict(marker="^", color="tab:green", s=80),
}

# Colours of the stages of the network in the figures of the stock
STAGE_COLOURS = {"Plants": "tab:blue", "Central warehouse": "tab:gray", "Regional warehouses": "tab:olive",
                 "Local warehouses": "tab:cyan"}


# ---------------------------------------------------------------------------
# The network by stages
# ---------------------------------------------------------------------------

def _on(point, route) -> bool:
    """True if a point lies on a route of horizontal and vertical stretches."""
    x, y = point
    for (x0, y0), (x1, y1) in zip(route[:-1], route[1:]):
        if min(x0, x1) - 0.5 <= x <= max(x0, x1) + 0.5 and min(y0, y1) - 0.5 <= y <= max(y0, y1) + 0.5:
            return True
    return False


@_light
def network(nodes: list, arcs: list, node_text: dict, arc_text: dict, title: str, full=(), idle=(),
            text_colour: str = SHORT, arc_list: list = ARCS_M4, legend: bool = False) -> None:
    """The network by stages, as figure CS-F1 of the statement. ``nodes`` are the
    nodes drawn and ``arcs`` the positions in ``arc_list`` of the arcs drawn;
    ``node_text`` gives the text under the label of each node and ``arc_text`` the
    text on each arc. The arcs in ``full`` are drawn in red, those in ``idle`` in
    light grey and with no text. With ``legend``, a legend of the arcs."""
    g = json.loads(NETWORK_FIGURE.read_text(encoding="utf-8"))
    places = {g["nodes"][n]["place"] for n in nodes}
    right = 1664 if any(n in RETAILERS for n in nodes) else 1320
    fig, ax = plt.subplots(figsize=(16.6 * right / 1664, 7.6))
    for node in nodes:
        d = g["nodes"][node]
        x0, y0, x1, y1 = d["bbox"]
        cx, cy = d["pos"]
        shape = {"transform": lambda: Rectangle((x0, y0), x1 - x0, y1 - y0),
                 "stock": lambda: Polygon([(cx, y0), (x1, y1), (x0, y1)]),
                 "transit": lambda: Circle((cx, cy), (x1 - x0) / 2),
                 "demand": lambda: Polygon([(cx, y0), (x1, cy), (cx, y1), (x0, cy)])}[d["kind"]]()
        shape.set(facecolor=FILL, edgecolor=INK, linewidth=1.4, zorder=3)
        ax.add_patch(shape)
    drawn = []
    for a in arcs:
        route, arc = g["arcs"][a], arc_list[a]
        assert (route["from"], route["to"]) == (arc["origin"], arc["destination"])
        points = route["pts"]
        drawn.append(points)
        colour = SHORT if a in full else (IDLE if a in idle else INK)
        xs, ys = zip(*points)
        # on a stretch that several arcs share, a full arc is drawn above the others and an idle arc below
        z = 2.2 if a in full else (1.8 if a in idle else 2)
        ax.plot(xs, ys, color=colour, lw=1.6 if a in full else 1.2, ls=(0, (5, 3)) if arc["mode"] == "Rail" else "-",
                zorder=z)
        ax.annotate("", xy=points[-1], xytext=points[-2], arrowprops=dict(arrowstyle="-|>", color=colour, lw=1.2),
                    zorder=z)
        if a in idle or not arc_text.get(a):
            continue
        if arc["destination"] in RETAILERS:
            # on the last stretch, next to the head: the stretches before it can be shared
            (x0, y0), (x1, y1) = points[-2], points[-1]
            where = (x1 - 48, y1)
        else:
            (x0, y0), (x1, y1) = max(zip(points[:-1], points[1:]),
                                     key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
            where = ((x0 + x1) / 2, (y0 + y1) / 2)
        ax.text(*where, arc_text[a], fontsize=7.5, ha="center", va="center", zorder=4,
                color=SHORT if a in full else text_colour, bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none"))
    for x, y in g["dots"]:                     # where two drawn arcs part
        if sum(_on((x, y), points) for points in drawn) > 1:
            ax.add_patch(Circle((x, y), 3, color=INK, zorder=3))
    align = {"end": "right", "start": "left", "middle": "center", None: "left"}
    for label in g["labels"]:
        if label["s"] in nodes or label["s"] in places:
            ax.text(label["x"], label["y"], label["s"], fontsize=9.5, ha=align[label["anchor"]], va="baseline",
                    style="italic" if label["italic"] else "normal", color=TEXT)
    for node in nodes:
        d = g["nodes"][node]
        name, place = (next(L for L in g["labels"] if L["s"] == s) for s in (node, d["place"]))
        if node == CENTRAL:                    # its label is above the node: the text goes above its name
            where, va = (name["x"], name["y"] - 22), "bottom"
        else:
            where, va = (place["x"], place["y"] + 12), "top"
        ax.text(*where, node_text.get(node, ""), fontsize=8, color=text_colour, ha=align[place["anchor"]], va=va,
                linespacing=1.15)
    if legend:
        handles = [Line2D([], [], color=INK, lw=1.2, label="road"),
                   Line2D([], [], color=INK, lw=1.2, ls=(0, (5, 3)), label="rail"),
                   Line2D([], [], color=SHORT, lw=1.6, label="arc capacity full"),
                   Line2D([], [], color=IDLE, lw=1.2, label="no flow")]
        ax.legend(handles=handles, fontsize=8, loc="lower left", frameon=False)
    ax.set_xlim(0, right)
    ax.set_ylim(650, -40)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(title, fontsize=10, color=TEXT)
    fig.tight_layout()
    plt.show()


def data_text(node: str, stock: bool = False, lost_sale: bool = False) -> str:
    """The data of M3 and M4 at a node, as written under its label. With ``stock``,
    the initial stock and the required final stock of the plants; with
    ``lost_sale``, the lost-sale cost of the retailers."""
    if node in F:
        ends = f"\nstock {_number(h_node_0_m4[node])} → {_number(h_node_end_m4[node])} bikes" if stock else ""
        return (f"{_number(c[node])} €/bike · {_number(K[node][T[0]])} bikes/month\n"
                f"{_number(c_h[node])} €/(bike·month) · {_number(K_h[node])} bikes" + ends)
    if node in RETAILERS:
        return (f"backorder share {_number(BACKORDER_SHARE[node], 1)}"
                + (f"\nlost-sale cost {_number(c_l[node])} €/bike" if lost_sale else ""))
    if node == RAIL_TERMINAL:
        return ""
    text = f"{_number(c_h_node_m4[node])} €/(bike·month) · {_number(K_h_node_m4[node])} bikes"
    return text + (f"\nnode capacity {_number(K_n[node])} bikes/month" if node in K_n else "")


def warehouses_empty(nodes: list) -> bool:
    """True if every warehouse among ``nodes`` starts and ends the six months with
    no stock, as in the data of M3 and M4."""
    return all(h_node_0_m4[i] == 0 and h_node_end_m4[i] == 0 for i in nodes if i not in F and i not in RETAILERS)


def arc_text(arc: dict) -> str:
    """The data of an arc, as written on it: transport cost (€/bike) and arc
    capacity (bikes/month); on the arcs to the retailers, which all have the same
    arc capacity, the transport cost only."""
    if arc["destination"] in RETAILERS:
        return _number(arc["cost"], 2)
    return f"{_number(arc['cost'], 2)} · {_number(arc['capacity'])}"


def _arriving(solution: dict, node: str, month: str) -> float:
    return sum(solution["flow"][a, month] for a, arc in enumerate(solution["arcs"]) if arc["destination"] == node)


def full_arcs(solution: dict, month: str) -> list:
    """The arcs whose capacity the plan uses entirely in a month (positions)."""
    return [a for a, arc in enumerate(solution["arcs"])
            if solution["flow"][a, month] > 1e-6 and abs(solution["flow"][a, month] - arc["capacity"]) < 1e-6]


def full_capacities(solution: dict, month: str, nodes: list, storage: dict, node_capacity: dict = K_n) -> list:
    """The capacities that the plan uses entirely in a month, with their shadow
    prices (€/bike): (capacity, shadow price), arcs first, then node capacities,
    then storage capacities."""
    out = [(f"Arc {a + 1} ({solution['arcs'][a]['origin']} → {solution['arcs'][a]['destination']})",
            solution["arc price"][a, month]) for a in full_arcs(solution, month)]
    out += [(f"Node capacity, {i}", solution["node price"][i, month]) for i in node_capacity
            if abs(_arriving(solution, i, month) - node_capacity[i]) < 1e-6]
    out += [(f"Storage capacity, {i}", solution["storage price"][i, month]) for i in nodes
            if storage.get(i, 0) > 0 and abs(solution["stock"][i, month] - storage[i]) < 1e-6]
    return out


def flow_network(solution: dict, month: str, nodes: list, node_text: dict, title: str) -> None:
    """The network by stages with the flow of each arc in one month: an arc whose
    capacity is full in red, an arc with no flow in light grey."""
    arcs = range(len(solution["arcs"]))
    flows = {a: solution["flow"][a, month] for a in arcs}
    network(nodes, arcs, node_text, {a: _number(v) for a, v in flows.items()}, title,
            full=full_arcs(solution, month), idle=[a for a, v in flows.items() if v <= 1e-6], text_colour=INK,
            arc_list=solution["arcs"], legend=True)


# ---------------------------------------------------------------------------
# The places of a network on the map
# ---------------------------------------------------------------------------

def peninsula(ax, window: tuple | None = None) -> None:
    """The outline of the Iberian Peninsula under a map: Spain in light grey,
    Portugal, France and Andorra lighter, the sea in light blue; no axes. ``window``
    is (west, south, east, north) in degrees; by default, the whole peninsula."""
    g = json.loads(PENINSULA.read_text(encoding="utf-8"))
    west, south, east, north = window or g["window"]
    for country, rings in g["countries"].items():
        for ring in rings:
            ax.add_patch(Polygon(ring, closed=True, facecolor=SPAIN if country == "Spain" else NEIGHBOUR,
                                 edgecolor="white", linewidth=0.6, zorder=0))
    ax.set_facecolor(SEA)
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_aspect(1.3)                         # a degree of longitude is 0,77 of one of latitude at 40° N
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


# Where a label can go around its point, in points: to the right, to the left,
# above, below and in the corners; then the same farther away, with a leader line
_AROUND = [(5, 0, "left", "center"), (-5, 0, "right", "center"), (0, 6, "center", "bottom"),
           (0, -6, "center", "top"), (5, 5, "left", "bottom"), (5, -5, "left", "top"),
           (-5, 5, "right", "bottom"), (-5, -5, "right", "top")]
_PLACES = [(dx * k, dy * k, ha, va, k > 1) for k in (1, 2.5, 4, 6) for dx, dy, ha, va in _AROUND]

# The cities around Madrid, too close to each other on the map of the expanded
# network for the search below: their labels are placed by hand, in points from
# the point, with a leader line
BY_HAND = {"Madrid": (-16, -1, "right", "center"), "Getafe": (-12, -12, "right", "top"),
           "Alcobendas": (-12, 11, "right", "bottom"), "Guadalajara": (6, 5, "left", "bottom"),
           "Alcalá de Henares": (8, -8, "left", "top")}


def place_labels(ax, labels: list, points: list, lines=(), fontsize: float = 7.5, colour: str = TEXT,
                 by_hand: dict | None = None) -> None:
    """Write each label of ``labels``, (text, (x, y)), next to its point, where it
    covers no other label, no point of ``points``, (x, y, size in points), no line
    of ``lines`` (lists of (x, y)) and not the legend. The first free place is taken,
    the nearest first; a place away from the point has a leader line. If none is
    free, the place that covers least. The labels of ``by_hand``, text: (dx, dy, ha,
    va), go first, where it says."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    to_screen = ax.transData.transform
    scale = fig.dpi / 72
    marks = []
    for x, y, size in points:
        px, py = to_screen((x, y))
        r = size * scale / 2 + 1
        marks.append((px - r, py - r, px + r, py + r))
    for line in lines:                          # a line is a row of small marks along it
        for (x0, y0), (x1, y1) in zip(line[:-1], line[1:]):
            (p0, q0), (p1, q1) = to_screen((x0, y0)), to_screen((x1, y1))
            n = max(2, int(((p1 - p0) ** 2 + (q1 - q0) ** 2) ** 0.5 / 4))
            for k in range(1, n):
                px, py = p0 + (p1 - p0) * k / n, q0 + (q1 - q0) * k / n
                marks.append((px - 1, py - 1, px + 1, py + 1))
    box = ax.get_window_extent(renderer)
    taken = []
    if ax.get_legend() is not None:
        b = ax.get_legend().get_window_extent(renderer)
        taken.append((b.x0, b.y0, b.x1, b.y1))

    def covered(b) -> float:
        """How much of the label a place covers: what it covers of the others, or
        everything if it leaves the map."""
        if b.x0 < box.x0 or b.x1 > box.x1 or b.y0 < box.y0 or b.y1 > box.y1:
            return float("inf")
        return sum(max(0, min(b.x1, m[2]) - max(b.x0, m[0])) * max(0, min(b.y1, m[3]) - max(b.y0, m[1]))
                   for m in marks + taken)

    by_hand = by_hand or {}
    for text, (x, y) in sorted(labels, key=lambda label: label[0] not in by_hand):
        if text in by_hand:
            dx, dy, ha, va = by_hand[text]
            t = ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                            fontsize=fontsize, color=colour, zorder=5,
                            arrowprops=dict(arrowstyle="-", color="0.45", lw=0.5, shrinkA=0, shrinkB=3))
            b = t.get_window_extent(renderer)
            taken.append((b.x0, b.y0, b.x1, b.y1))
            continue
        best = None
        for dx, dy, ha, va, far in _PLACES:
            t = ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va,
                            fontsize=fontsize, color=colour, zorder=5,
                            arrowprops=dict(arrowstyle="-", color="0.45", lw=0.5, shrinkA=0, shrinkB=3)
                            if far else None)
            b = t.get_window_extent(renderer)
            cover = covered(b)
            t.remove()
            if best is None or cover < best[0]:
                best = (cover, dx, dy, ha, va, far)
            if cover == 0:
                break
        _, dx, dy, ha, va, far = best
        t = ax.annotate(text, (x, y), xytext=(dx, dy), textcoords="offset points", ha=ha, va=va, fontsize=fontsize,
                        color=colour, zorder=5,
                        arrowprops=dict(arrowstyle="-", color="0.45", lw=0.5, shrinkA=0, shrinkB=3) if far else None)
        b = t.get_window_extent(renderer)
        taken.append((b.x0, b.y0, b.x1, b.y1))


@_light
def places_map(places: list, title: str, window: tuple | None = None, figsize=(8.6, 6.6),
               by_hand: dict | None = None) -> None:
    """The places of a network on the outline of the peninsula: ``places`` is a list
    of (kind, city, latitude, longitude), with ``kind`` one of ``KINDS``. One symbol
    for each kind, with its legend, and the city as the only label. Elements in the
    same city are drawn side by side, and the city is written once. ``by_hand``:
    labels placed by hand, as in ``place_labels``."""
    fig, ax = plt.subplots(figsize=figsize)
    peninsula(ax, window)
    at = {}
    for kind, city, lat, lon in places:
        at.setdefault((lat, lon), []).append(kind)
    points, labels, shown = [], [], set()
    for (lat, lon), kinds in at.items():
        for k, kind in enumerate(kinds):
            x = lon + 0.17 * (k - (len(kinds) - 1) / 2)        # side by side, about one symbol apart
            style = KINDS[kind]
            ax.scatter(x, lat, marker=style["marker"], color=style["color"], s=style["s"], edgecolors="white",
                       linewidths=0.6, zorder=3)
            points.append((x, lat, style["s"] ** 0.5 + 1))
    for kind, city, lat, lon in places:
        if city not in shown:
            shown.add(city)
            group = at[(lat, lon)]
            labels.append((city, (lon + 0.17 * (len(group) - 1) / 2, lat)))
    for kind in dict.fromkeys(kind for kind, *_ in places):
        style = KINDS[kind]
        ax.scatter([], [], marker=style["marker"], color=style["color"], s=style["s"], label=kind)
    ax.legend(fontsize=7.5, loc="lower right", framealpha=0.9)
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    place_labels(ax, labels, points, by_hand=by_hand)
    plt.show()


# ---------------------------------------------------------------------------
# Panels of a plan by month
# ---------------------------------------------------------------------------

def inside(ax, x: float, bottom: float, value: float, colour: str = "black", top: float | None = None,
           fontsize: float = 7, avoid=()) -> None:
    """The number of a bar or of a part of a stacked bar, in its middle; nothing if
    the part is too thin for it. ``avoid`` gives the heights of the points drawn on
    the bar: the number moves away from them within the part."""
    top = top or ax.get_ylim()[1]
    if value <= 0.045 * top:
        return

    def gap(y: float) -> float:
        return min((abs(y - a) for a in avoid), default=top)

    y = bottom + value / 2
    if gap(y) < 0.07 * top:
        room = [bottom + value * k / 10 for k in range(2, 9)]
        room = [c for c in room if bottom + 0.025 * top <= c <= bottom + value - 0.025 * top]
        if room:
            y = max(room, key=gap)
    ax.text(x, y, _number(value), ha="center", va="center", fontsize=fontsize, color=colour)


def stacked(ax, months: list, rows: dict, colours: dict, top: float | None = None, width: float = 0.62,
            totals: bool = True, hatch: dict | None = None, x0: float = 0.0, avoid: list | None = None) -> list:
    """Bars stacked by month, one part for each row of ``rows`` (label: values by
    month), with the number of each part inside it and, with ``totals``, the total
    above the bar. ``avoid`` gives, by month, the heights of the points drawn on the
    bar, which the numbers do not cover. Returns the totals."""
    x = [i + x0 for i in range(len(months))]
    bottom = [0.0] * len(months)
    parts = []
    for label, values in rows.items():
        hatched = (hatch or {}).get(label)
        ax.bar(x, values, width, bottom=bottom, color=colours[label], label=label, hatch=hatched,
               alpha=0.55 if hatched else None, edgecolor="white" if hatched else None)
        parts.append((label, list(values), list(bottom)))
        bottom = [b + v for b, v in zip(bottom, values)]
    top = top or max(max(bottom) * 1.15, 1)
    ax.set_ylim(0, top)
    for label, values, below in parts:
        for i, v in enumerate(values):
            inside(ax, x[i], below[i], v, top=top, avoid=avoid[i] if avoid else (), fontsize=7 if width > 0.5 else 6.5)
    if totals:
        for i, total in enumerate(bottom):
            if total > 0:
                ax.text(x[i], total + top * 0.012, _number(total), ha="center", va="bottom", fontsize=7.5,
                        weight="bold")
    ax.set_xticks(range(len(months)), months)
    ax.spines[["top", "right"]].set_visible(False)
    return bottom


@_light
def orders_figure(rows: dict, title: str, ylabel: str = "Orders (bikes)", price: dict | None = None) -> None:
    """The orders of each month, stacked by customer (``rows``: customer: orders by
    month), with the orders of each customer inside its part of the bar and the
    total above it. With ``price``, a panel above with the price of each month."""
    if price:
        fig, (above, ax) = plt.subplots(2, 1, figsize=(11, 6), sharex=True, gridspec_kw={"height_ratios": [1, 3.2]})
    else:
        fig, ax = plt.subplots(figsize=(11, 4.6))
    colours = plt.get_cmap("Set2")
    bottom = [0] * len(T)
    for k, (name, values) in enumerate(rows.items()):
        ax.bar(range(len(T)), values, 0.62, bottom=bottom, color=colours(k), label=name)
        for i, v in enumerate(values):
            ax.text(i, bottom[i] + v / 2, _number(v), ha="center", va="center", fontsize=7.5)
        bottom = [b + v for b, v in zip(bottom, values)]
    for i, total in enumerate(bottom):
        ax.text(i, total + max(bottom) * 0.015, _number(total), ha="center", va="bottom", fontsize=8.5,
                weight="bold")
    ax.set_xticks(range(len(T)), T)
    ax.set_ylim(0, max(bottom) * 1.1)
    ax.set_ylabel(ylabel)
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    ax.spines[["top", "right"]].set_visible(False)
    if price:
        values = [price[t] for t in T]
        above.plot(range(len(T)), values, color="black", marker="o", lw=1.2)
        for i, v in enumerate(values):
            above.annotate(_number(v), (i, v), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=7.5)
        above.set_ylim(0, max(values) * 1.35)
        above.set_ylabel("Price\n(€/bike)")
        above.set_title(title, fontsize=10)
        above.spines[["top", "right"]].set_visible(False)
    else:
        ax.set_title(title, fontsize=10)
    fig.tight_layout()
    plt.show()


def step(ax, months: list, values: list, **style) -> None:
    """A value by month as a line of steps, one step on each bar."""
    ax.step([-0.5, *range(len(months)), len(months) - 0.5], [values[0], *values, values[-1]], where="mid", **style)


@_light
def assembly_figure(assembly: dict, capacity: dict, months: list, plants: list, title: str,
                    overtime: dict | None = None, overtime_limit: dict | None = None, closed=()) -> None:
    """One panel for each plant: the bikes it assembles in each month against its
    capacity, a dashed line. With ``overtime``, the part assembled in overtime is
    hatched on top, and the capacity plus the overtime limit is a dotted line. A
    plant in ``closed`` assembles nothing."""
    top = max(max(capacity[f][t] + (overtime_limit or {}).get(f, 0) for t in months) for f in plants) * 1.22
    fig, axes = plt.subplots(1, len(plants), figsize=(15, 3.6), sharey=True)
    x = range(len(months))
    for ax, f in zip(axes, plants):
        extra = [overtime[f, t] if overtime else 0.0 for t in months]
        regular = [assembly[f, t] - e for t, e in zip(months, extra)]
        ax.bar(x, regular, 0.6, color=COLOURS[f], label="assembly in regular time" if overtime else "assembly")
        if overtime and any(extra):
            ax.bar(x, extra, 0.6, bottom=regular, color=COLOURS[f], alpha=0.45, hatch="///", edgecolor="white",
                   label="assembly in overtime")
        ax.set_ylim(0, top)
        for i in x:
            inside(ax, i, 0, regular[i], colour="white", top=top)
            inside(ax, i, regular[i], extra[i], top=top)
        if f in closed:
            ax.text(0.5, 0.5, "plant closed", transform=ax.transAxes, ha="center", va="center", fontsize=9,
                    color=SHORT)
            ax.set_xticks(list(x), months)
            ax.set_title(f, fontsize=10)
            ax.spines[["top", "right"]].set_visible(False)
            continue
        step(ax, months, [capacity[f][t] for t in months], color="black", lw=1, ls="--", label="capacity")
        if overtime_limit and overtime_limit.get(f):
            step(ax, months, [capacity[f][t] + overtime_limit[f] for t in months], color="black", lw=1, ls=":",
                 label="capacity plus overtime limit")
        ax.set_xticks(list(x), months)
        ax.set_title(f, fontsize=10)
        ax.legend(fontsize=7, loc="upper left", frameon=False, ncol=2)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Bikes per month")
    fig.suptitle(title, fontsize=11)
    fig.tight_layout()
    plt.show()


def stage_stock(ax, stock: dict, months: list, rented: dict | None = None) -> None:
    """The stock at each stage of the network at the end of each month, stacked
    (``stock``: stage: values by month); with ``rented``, the part of the central
    warehouse in rented storage is hatched."""
    rows = {}
    for stage, values in stock.items():
        if stage == "Central warehouse" and rented:
            rows["Central warehouse, own storage"] = [v - rented[t] for v, t in zip(values, months)]
            rows["Central warehouse, rented storage"] = [rented[t] for t in months]
        else:
            rows[stage] = values
    colours = {**STAGE_COLOURS, "Central warehouse, own storage": STAGE_COLOURS["Central warehouse"],
               "Central warehouse, rented storage": STAGE_COLOURS["Central warehouse"]}
    hatch = {"Central warehouse, rented storage": "///"}
    totals = [sum(v[i] for v in rows.values()) for i in range(len(months))]
    stacked(ax, months, rows, colours, top=max(max(totals) * 1.2, 10), hatch=hatch)
    ax.set_ylabel("Bikes at the end of the month")
    ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=2, frameon=False)


def shadow_prices(ax, prices: list, month: str) -> None:
    """The shadow prices of the capacities that are full in one month, one bar for
    each capacity (``prices``: (capacity, price)); a text if none is full."""
    title = (f"Shadow prices of the full capacities in {month} (€/bike)\n"
             "Full capacity: the plan uses all of it in the month. Shadow price:\n"
             "the change in the cost of the plan with one more bike of that\n"
             "capacity in that month; negative, a saving")
    ax.set_title(title, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    if not prices:
        ax.text(0.5, 0.5, f"No capacity is full in {month}", transform=ax.transAxes, ha="center", va="center",
                fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        return
    names = [name for name, _ in prices][::-1]
    values = [value for _, value in prices][::-1]
    ax.barh(range(len(names)), values, 0.6, color=["tab:green" if v < 0 else "0.6" for v in values])
    ax.axvline(0, color="black", lw=0.8)
    low = min(min(values), 0)
    ax.set_xlim(low * 1.35 - 1, max(max(values), 0) * 1.35 + 1)
    for i, v in enumerate(values):
        ax.text(v, i, f" {_number(v, 2)} ", ha="right" if v < 0 else "left", va="center", fontsize=7.5)
    ax.set_yticks(range(len(names)), names, fontsize=7.5)
    ax.set_xlabel("€/bike")
