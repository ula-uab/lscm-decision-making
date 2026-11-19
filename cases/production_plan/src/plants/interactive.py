"""Interactive figures for the notebooks, drawn with Plotly.

Each function returns a Plotly figure, and ``show`` draws it. The figures take
the width of the cell, so that they can be read on a tablet or a phone; the
values are in the label that appears on placing the pointer on a bar, a node or
an arc (or on touching it), and the legend goes under the figure.

``dropdown_figure`` joins several figures, one per option, into one figure with
a dropdown at its top left. The dropdown is part of the figure: changing the
option runs no Python, so nothing is computed again, and every option is
computed before the figure is drawn. A dropdown of ipywidgets would run Python
at each change, but Google Colab does not draw a Plotly figure in a cell that
shows an ipywidgets dropdown.

The colours are those of the figures drawn with matplotlib (``figures``), so that
each colour keeps its meaning: red, a full capacity; light grey, an arc with no
flow; one colour for each plant and for each stage of the network.
"""

from __future__ import annotations

import json
import math
import sys

import plotly.graph_objects as go
from matplotlib.colors import to_hex

from . import figures
from .show import _number

TOP = 120          # top margin (px) of a figure with a dropdown: the dropdown at its top, the title under it
FULL = to_hex("tab:red")
IDLE = to_hex(figures.IDLE)
INK, TEXT, FILL = figures.INK, figures.TEXT, figures.FILL
MONTH_HEIGHT = 380 # height (px) of a figure of values by month
LAYOUT = dict(template="plotly_white", separators=",.", font=dict(size=12, color=TEXT), hoverlabel=dict(font_size=12),
              margin=dict(t=56, b=40, l=56, r=16))
# The layout that each option of a dropdown sets, where its figure has it
OPTION_LAYOUT = ("title.text", "shapes", "annotations", "xaxis.range", "yaxis.range", "yaxis.title.text",
                 "xaxis.title.text", "yaxis.tickvals", "yaxis.ticktext")


def colour(name: str) -> str:
    """A colour of matplotlib ("tab:blue", "0.78") as Plotly takes it."""
    return to_hex(name)


def show(fig: go.Figure) -> None:
    """Show a Plotly figure: in Colab, as Plotly shows it there; elsewhere as HTML,
    with the Plotly library from the internet, which PyCharm draws."""
    if "google.colab" in sys.modules:
        fig.show(config={"displaylogo": False})
        return
    from IPython.display import HTML, display
    display(HTML(fig.to_html(include_plotlyjs="cdn", full_html=False, config={"displaylogo": False})))


def _legend_below(fig: go.Figure) -> None:
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.14, x=0, font_size=11, traceorder="normal"))


def _get(layout, path: str):
    for key in path.split("."):
        layout = getattr(layout, key, None)
        if layout is None:
            return None
    return layout


def _menu_on_top(fig: go.Figure, buttons: list, active: int) -> None:
    """A dropdown at the top left of a figure, and its title just under it."""
    height = fig.layout.height or MONTH_HEIGHT
    plot = height - TOP - (fig.layout.margin.b or 0)        # height of the plotting area (px)
    fig.update_layout(margin_t=TOP, title=dict(yref="paper", y=1, yanchor="bottom", pad=dict(b=10)),
                      updatemenus=[dict(buttons=buttons, active=active, x=0, xanchor="left", y=1 + (TOP - 6) / plot,
                                        yanchor="top", font_size=12)])


def dropdown_figure(figures_: dict, first=None) -> go.Figure:
    """One figure with a dropdown that shows one of ``figures_`` (label: Plotly
    figure): its traces and the parts of its layout in ``OPTION_LAYOUT``. ``first``
    is the label shown first; by default, the first."""
    labels = list(figures_)
    first = labels.index(first) if first is not None else 0
    fig = go.Figure()
    owner = []                                   # the option of each trace
    for k, f in enumerate(figures_.values()):
        for trace in f.data:
            fig.add_trace(trace.update(visible=(k == first)))
            owner.append(k)

    def layout_of(f):
        out = {path: _get(f.layout, path) for path in OPTION_LAYOUT}
        out["shapes"], out["annotations"] = out["shapes"] or [], out["annotations"] or []
        return {path: value for path, value in out.items() if value is not None}

    buttons = [dict(label=label, method="update", args=[{"visible": [o == k for o in owner]}, layout_of(f)])
               for k, (label, f) in enumerate(figures_.items())]
    fig.update_layout(figures_[labels[first]].layout)
    _menu_on_top(fig, buttons, first)
    return fig


def bars(x: list, rows: dict, colours: dict, title: str, ytitle: str = "bikes", line=None,
         line_label: str = "", totals: bool = True, unit: str = "bikes", inside: bool = False,
         top: float | None = None, legend: bool = True) -> go.Figure:
    """Bars by month, stacked by row (``rows``: label: values), each row in its
    colour; with ``totals``, the total above each bar; with ``line``, a dashed line
    at that value or, with one value per month, in steps, named ``line_label``; with
    ``inside``, the value of each part inside it. The value of each part is in its
    label."""
    if isinstance(line, (list, tuple)) and len(set(line)) == 1:
        line = line[0]
    fig = go.Figure()
    for label, values in rows.items():
        fig.add_bar(x=x, y=values, name=label, marker_color=colours[label], showlegend=legend and len(rows) > 1,
                    text=[_number(v) if v else "" for v in values] if inside else None,
                    textposition="inside" if inside else None, insidetextanchor="middle",
                    hovertemplate=f"{label}<br>%{{x}}: %{{y:,.0f}} {unit}<extra></extra>")
    total = [sum(values[i] for values in rows.values()) for i in range(len(x))]
    if totals and len(rows) > 1:
        fig.add_scatter(x=x, y=total, mode="text", text=[_number(v) for v in total], textposition="top center",
                        showlegend=False, hoverinfo="skip", textfont=dict(size=12, color=TEXT))
    steps = isinstance(line, (list, tuple))
    highest = max(max(total), max(line) if steps else (line or 0), 1)
    if steps:
        # one step on each bar: the category axis puts bar k between k - 0,5 and k + 0,5
        fig.add_scatter(x=[k + d for k in range(len(x)) for d in (-0.5, 0.5)], y=[v for v in line for _ in (0, 1)],
                        xaxis="x2", mode="lines", line=dict(color="black", width=1, dash="dash"), name=line_label,
                        hovertemplate=f"{line_label}: %{{y:,.0f}} {unit}<extra></extra>")
        fig.update_layout(xaxis2=dict(overlaying="x", range=[-0.5, len(x) - 0.5], visible=False))
    elif line is not None:
        fig.add_hline(y=line, line_dash="dash", line_color="black", line_width=1, annotation_text=line_label,
                      annotation_position="top left", annotation_font_size=11)
    fig.update_layout(**LAYOUT, barmode="stack", height=MONTH_HEIGHT, title=dict(text=title, font_size=14),
                      yaxis=dict(title=ytitle, range=[0, top or 1.15 * highest]))
    _legend_below(fig)
    return fig


def horizontal_bars(names: list, values: list, hover: list, title: str, xtitle: str, unit: str = "",
                    empty: str = "", rows: int | None = None) -> go.Figure:
    """One horizontal bar per name, the first at the top, with its value beside it
    and ``hover`` in its label; ``empty`` is the text when there are none. ``rows``
    sets the height for that many bars, so that the figures of a dropdown match."""
    fig = go.Figure()
    n = len(names)
    m = max(n, rows or 0, 1)                     # bar positions: the first at the top
    if n:
        fig.add_bar(y=[m - 1 - k for k in range(n)], x=values, width=0.6, orientation="h", marker_color=colour(figures.PRICE_BAR),
                    text=[_number(v, 2) for v in values], textposition="outside", customdata=hover,
                    hovertemplate=f"%{{customdata}}<br>%{{x:,.2f}} {unit}<extra></extra>", showlegend=False)
    low, high = min([*values, 0]), max([*values, 0])
    fig.update_layout(**LAYOUT, height=max(240, 130 + 34 * max(n, rows or 0)), title=dict(text=title, font_size=14),
                      xaxis=dict(title=xtitle, range=[low * 1.3 - 0.6, high * 1.3 + 0.6], zeroline=True,
                                 zerolinecolor="black"),
                      yaxis=dict(tickvals=[m - 1 - k for k in range(n)], ticktext=names, range=[-0.6, m - 0.4],
                                 automargin=True),
                      annotations=[] if n else [dict(text=empty, x=0.5, y=0.5, xref="paper", yref="paper",
                                                     showarrow=False, font_size=13)])
    return fig


# ---------------------------------------------------------------------------
# The places of a network on the map
# ---------------------------------------------------------------------------

SYMBOLS = {"s": "square", "v": "triangle-down", "o": "circle", "D": "diamond", "^": "triangle-up"}


def places_map(places: list, title: str, window: tuple | None = None, height: int = 520) -> go.Figure:
    """The places of a network on the outline of the peninsula: ``places`` is a list
    of (kind, name, city, latitude, longitude), with ``kind`` one of
    ``figures.KINDS``. One symbol for each kind, with its legend; the name, the city
    and the coordinates of each element in its label. Two buttons show or hide the
    names of the cities. Elements in the same city are drawn side by side."""
    g = json.loads(figures.PENINSULA.read_text(encoding="utf-8"))
    west, south, east, north = window or g["window"]
    fig = go.Figure()
    for country, rings in g["countries"].items():
        for ring in rings:
            xs, ys = zip(*ring)
            fig.add_scatter(x=xs, y=ys, mode="lines", fill="toself", hoverinfo="skip", showlegend=False,
                            fillcolor=figures.SPAIN if country == "Spain" else figures.NEIGHBOUR,
                            line=dict(color="white", width=0.6))
    at = {}
    for kind, name, city, lat, lon in places:
        at.setdefault((lat, lon), []).append(name)
    kinds = [k for k in figures.KINDS if any(p[0] == k for p in places)]
    labelled, shown = [], set()
    for kind in kinds:
        style = figures.KINDS[kind]
        rows = [p for p in places if p[0] == kind]
        xs = []
        text = []
        for _, name, city, lat, lon in rows:
            same = at[lat, lon]
            xs.append(lon + 0.17 * (same.index(name) - (len(same) - 1) / 2))     # side by side, one symbol apart
            text.append("" if city in shown else city)                            # each city written once
            shown.add(city)
        fig.add_scatter(x=xs, y=[p[3] for p in rows], mode="markers", name=kind, text=text,
                        textposition="top center", textfont=dict(size=11, color=TEXT),
                        marker=dict(symbol=SYMBOLS[style["marker"]], color=colour(style["color"]),
                                    size=round(1.5 * math.sqrt(style["s"])),
                                    line=dict(color=style.get("edge", "white"), width=1 if "edge" in style else 0.6)),
                        customdata=[[p[1], p[2], _number(p[3], 4), _number(p[4], 4)] for p in rows],
                        hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>"
                                      "latitude %{customdata[2]} · longitude %{customdata[3]}<extra></extra>")
        labelled.append(len(fig.data) - 1)
    plot = height - 90 - 4
    fig.update_layout(**LAYOUT, height=height, plot_bgcolor=figures.SEA, dragmode="pan",
                      title=dict(text=title, font_size=14, yref="container", y=1 - 10 / height, yanchor="top"),
                      xaxis=dict(range=[west, east], visible=False),
                      yaxis=dict(range=[south, north], visible=False, scaleanchor="x", scaleratio=1.3),
                      updatemenus=[dict(type="buttons", direction="right", x=0, xanchor="left", y=1 + 46 / plot,
                                        yanchor="top", showactive=True, active=1, font_size=12, buttons=[
                                            dict(label="City names", method="restyle",
                                                 args=[{"mode": "markers+text"}, labelled]),
                                            dict(label="No names", method="restyle",
                                                 args=[{"mode": "markers"}, labelled])])])
    fig.update_layout(margin=dict(t=90, l=4, r=4, b=4))
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-0.01, x=0, font_size=11))
    return fig


# ---------------------------------------------------------------------------
# The network by stages
# ---------------------------------------------------------------------------

def _node_shapes(g: dict, nodes: list, fill: dict) -> list:
    shapes = []
    for node in nodes:
        d = g["nodes"][node]
        x0, y0, x1, y1 = d["bbox"]
        cx, cy = d["pos"]
        style = dict(fillcolor=fill.get(node, FILL), line=dict(color=INK, width=1.4), layer="above")
        if d["kind"] == "transform":
            shapes.append(dict(type="rect", x0=x0, y0=y0, x1=x1, y1=y1, **style))
        elif d["kind"] == "stock":
            shapes.append(dict(type="path", path=f"M {cx},{y0} L {x1},{y1} L {x0},{y1} Z", **style))
        elif d["kind"] == "transit":
            shapes.append(dict(type="circle", x0=x0, y0=y0, x1=x1, y1=y1, **style))
        else:
            shapes.append(dict(type="path", path=f"M {cx},{y0} L {x1},{cy} L {cx},{y1} L {x0},{cy} Z", **style))
    return shapes


def network(nodes: list, arc_list: list, options: dict, first=None, legend: dict | None = None,
            height: int = 500) -> go.Figure:
    """The network by stages, as figure CS-F1 of the statement, with the name of each
    node beside it. ``options`` gives, by label of the dropdown (one option: no
    dropdown), a dict with "title"; "arc_text" (arc: text written on it);
    "arc_hover" and "node_hover" (the label of each arc and node); and, optionally,
    "full" and "idle" (arcs drawn red and light grey, with no text) and "fill"
    (node: colour). ``legend`` adds, under the figure, a filled square for each
    label: colour."""
    g = json.loads(figures.NETWORK_FIGURE.read_text(encoding="utf-8"))
    labels = list(options)
    first = labels.index(first) if first is not None else 0
    align = {"end": "right", "start": "left", "middle": "center"}
    names = [dict(x=L["x"], y=L["y"], text=L["s"], showarrow=False, xanchor=align.get(L["anchor"], "left"),
                  yanchor="bottom", bgcolor="white", font=dict(size=11, color=TEXT))
             for L in g["labels"] if L["s"] in nodes]
    fig = go.Figure()
    owner, layouts = [], []
    for k, option in enumerate(options.values()):
        full, idle = set(option.get("full", ())), set(option.get("idle", ()))
        notes, drawn, hx, hy, ht = [], [], [], [], []
        for a, arc in enumerate(arc_list):
            route = g["arcs"][a]
            assert (route["from"], route["to"]) == (arc["origin"], arc["destination"])
            pts = route["pts"]
            drawn.append(pts)
            c = FULL if a in full else (IDLE if a in idle else INK)
            xs, ys = zip(*pts)
            fig.add_scatter(x=xs, y=ys, mode="lines", hoverinfo="skip", showlegend=False, visible=(k == first),
                            line=dict(color=c, width=2 if a in full else 1.4,
                                      dash="dash" if arc["mode"] == "Rail" else "solid"))
            owner.append(k)
            (xa, ya), (xb, yb) = pts[-2], pts[-1]
            notes.append(dict(x=xb, y=yb, ax=xa, ay=ya, xref="x", yref="y", axref="x", ayref="y", text="",
                              showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=1.4, arrowcolor=c, standoff=0))
            p0, p1 = max(zip(pts[:-1], pts[1:]), key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
            mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
            if option["arc_text"].get(a) and a not in idle:
                notes.append(dict(x=mx, y=my, text=option["arc_text"][a], showarrow=False, bgcolor="white",
                                  font=dict(size=11, color=FULL if a in full else INK)))
            hx.append(mx)
            hy.append(my)
            ht.append(option["arc_hover"][a])
        fig.add_scatter(x=hx, y=hy, mode="markers", marker=dict(size=16, opacity=0), hovertext=ht, hoverinfo="text",
                        showlegend=False, visible=(k == first))
        owner.append(k)
        shown = [n for n in nodes if option["node_hover"].get(n)]
        fig.add_scatter(x=[g["nodes"][n]["pos"][0] for n in shown], y=[g["nodes"][n]["pos"][1] for n in shown],
                        mode="markers", marker=dict(size=34, opacity=0), hovertext=[option["node_hover"][n] for n in shown],
                        hoverinfo="text", showlegend=False, visible=(k == first))
        owner.append(k)
        dots = [dict(type="circle", x0=x - 3, y0=y - 3, x1=x + 3, y1=y + 3, fillcolor=INK, line_width=0)
                for x, y in g["dots"] if sum(figures._on((x, y), p) for p in drawn) > 1]
        layouts.append({"annotations": names + notes, "shapes": _node_shapes(g, nodes, option.get("fill", {})) + dots,
                        "title.text": option["title"]})
    # The legend: the arcs and, with ``legend``, the colours of the nodes; always shown
    keys = [("road", dict(color=INK, width=1.4)), ("rail", dict(color=INK, width=1.4, dash="dash")),
            ("arc capacity full", dict(color=FULL, width=2)), ("no flow", dict(color=IDLE, width=1.4))]
    if not any(o.get("full") or o.get("idle") for o in options.values()):
        keys = keys[:2]
    for name, line in keys:
        fig.add_scatter(x=[None], y=[None], mode="lines", line=line, name=name)
        owner.append(None)
    for name, c in (legend or {}).items():
        fig.add_scatter(x=[None], y=[None], mode="markers", name=name,
                        marker=dict(symbol="square", size=12, color=c, line=dict(color=INK, width=1)))
        owner.append(None)
    fig.update_layout(**LAYOUT, height=height, dragmode="pan", hovermode="closest",
                      annotations=layouts[first]["annotations"], shapes=layouts[first]["shapes"],
                      title=dict(text=layouts[first]["title.text"], font_size=14),
                      xaxis=dict(visible=False, range=[60, 1330]),
                      yaxis=dict(visible=False, range=[680, 20], scaleanchor="x"))
    fig.update_layout(margin=dict(t=56, l=4, r=4, b=4))
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=0, x=0, font_size=11))
    if len(options) > 1:
        buttons = [dict(label=label, method="update",
                        args=[{"visible": [o is None or o == k for o in owner]}, layouts[k]])
                   for k, label in enumerate(labels)]
        _menu_on_top(fig, buttons, first)
    return fig
