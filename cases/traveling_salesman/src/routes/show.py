"""What the notebook shows: tables, maps and short messages.

Each function answers one step of the notebook, so that its cells only need
one line of code. ``document_figures`` draws the maps of traveling_salesman.md;
from the folder of the case, with the environment of the repository:

    uv run python -c "import routes; routes.document_figures()"
"""

from __future__ import annotations

import functools
import math
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from . import construction as co
from . import exact as ex
from . import local_search as ls
from .data import ABBR, CITIES, HOME, NAME, XY, d

ROUTE = "tab:blue"
OUT = "tab:red"
IN = "tab:green"

STARTS = {"nearest neighbor": "nearest neighbor", "sweep": "sweep", "random": "random route"}
MOVE_NAMES = {label: key for key, label in ls.MOVES.items()}

# Where the abbreviation of each city is written, from its point (points); the
# cities of the cluster around Braunschweig need their own positions
_LABEL = {i: (5, 5) for i in CITIES}
_LABEL.update({3: (-12, 5), 4: (6, -10), 13: (-24, -12), 14: (2, -14)})


def _light(func):
    """Draw with matplotlib's default style: white background and dark text, also
    when the editor has a dark theme."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with plt.style.context("default"):
            return func(*args, **kwargs)
    return wrapper


def _display(obj) -> None:
    try:
        from IPython.display import display
        display(obj)
    except ImportError:
        print(obj)


def _km(x: float) -> str:
    return f"{x:,.0f} km"


def _move_key(move: str) -> str:
    """'reversal' for 'reversal' or for 'reversal of a sub-path'."""
    return MOVE_NAMES.get(move, move)


@functools.lru_cache(maxsize=1)
def _shortest() -> tuple[int, tuple]:
    length, routes = ex.shortest_routes()
    return length, tuple(tuple(r) for r in ex.distinct(routes))


# ---------------------------------------------------------------------------
# Maps
# ---------------------------------------------------------------------------

@_light
def plot_route(route: list[int] | None = None, ax=None, title: str = "", out=(), new=(), rays: bool = False):
    """Map of the cities, north up and the same scale on both axes, with a route
    (arrows in the order of the route). ``out`` are arcs drawn dashed in red
    (they leave the route) and ``new`` arcs drawn thick in green (they enter it).
    ``rays`` draws the line from home to each city, as in the sweep."""
    ax = ax or plt.subplots(figsize=(5.2, 5.4))[1]
    if rays:
        for i in CITIES:
            if i != HOME:
                ax.plot(*zip(XY[HOME], XY[i]), color="0.8", lw=0.8, zorder=1)
        ax.annotate("", xy=(XY[HOME][0], XY[HOME][1] + 120), xytext=XY[HOME],
                    arrowprops=dict(arrowstyle="->", color="0.5", ls=":"), zorder=1)
    if route:
        for a, b in zip(route, route[1:]):
            ax.annotate("", xy=XY[b], xytext=XY[a], zorder=2,
                        arrowprops=dict(arrowstyle="-|>", color=ROUTE, lw=1.4, shrinkA=6, shrinkB=6))
    for a, b in out:
        ax.plot(*zip(XY[a], XY[b]), color=OUT, lw=2.2, ls="--", zorder=3)
    for a, b in new:
        ax.plot(*zip(XY[a], XY[b]), color=IN, lw=3, alpha=0.7, zorder=3)
    for i in CITIES:
        ax.scatter(*XY[i], s=70 if i == HOME else 36, marker="s" if i == HOME else "o",
                   color="black" if i == HOME else "white", edgecolor="black", zorder=4)
        ax.annotate(ABBR[i], XY[i], xytext=_LABEL[i], textcoords="offset points", fontsize=8, zorder=5)
    if out or new:
        ax.plot([], [], color=OUT, lw=2.2, ls="--", label="arcs out")
        ax.plot([], [], color=IN, lw=3, alpha=0.7, label="arcs in")
        ax.legend(fontsize=8, loc="lower left", frameon=False)
    ax.annotate("N", xy=(0.06, 0.98), xytext=(0.06, 0.86), xycoords="axes fraction", ha="center", va="top",
                fontsize=9, arrowprops=dict(arrowstyle="-|>", color="black"))
    ax.set_aspect("equal")
    ax.set_xlim(40, 480)
    ax.set_ylim(-20, 560)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(title, fontsize=10)
    return ax


def _route_title(name: str, route: list[int]) -> str:
    return f"{name}: {_km(co.length(route))}"


# ---------------------------------------------------------------------------
# §1 Data
# ---------------------------------------------------------------------------

def cities_table() -> pd.DataFrame:
    """Table 1: number, name, abbreviation and coordinates of each city."""
    return pd.DataFrame({i: {"City": NAME[i], "Abbreviation": ABBR[i], "x": XY[i][0], "y": XY[i][1]}
                         for i in CITIES}).T.rename_axis("i")


def distance_table() -> pd.DataFrame:
    """Table 2: distance between each pair of cities (km)."""
    return pd.DataFrame({ABBR[j]: {ABBR[i]: d[i][j] for i in CITIES} for j in CITIES})


@_light
def show_data() -> None:
    """The cities, the distances, the number of routes and the map."""
    print("The cities and their coordinates:")
    _display(cities_table())
    print("Distance between each pair of cities (km):")
    _display(distance_table())
    n = len(CITIES) - 1
    print(f"From {NAME[HOME]} there are {n} cities to visit: {n}! = {math.factorial(n):,} orders of visit, "
          f"{math.factorial(n) // 2:,} different round trips if a route and the same route in the "
          "other direction count once.")
    plot_route(title="The 14 cities")
    plt.show()


# ---------------------------------------------------------------------------
# §3 Nearest neighbor
# ---------------------------------------------------------------------------

def legs_table(route: list[int]) -> pd.DataFrame:
    """One row per leg of a route, with the distance so far."""
    rows, total = [], 0
    for k, (a, b, km) in enumerate(co.legs(route), start=1):
        total += km
        rows.append({"From": ABBR[a], "To": ABBR[b], "Distance (km)": km, "So far (km)": total})
    return pd.DataFrame(rows, index=pd.RangeIndex(1, len(rows) + 1, name="Leg"))


@_light
def nearest_neighbor() -> list[int]:
    """§3: the route of the nearest neighbor, leg by leg, and its map."""
    route = co.nearest_neighbor()
    print("From HH, each time to the nearest city not yet visited; at the end, back to HH.")
    _display(legs_table(route))
    print(f"Route: {co.label(route)}. Length: {_km(co.length(route))}.")
    a, b, c = route[-3:]
    print(f"The last two legs, {ABBR[a]} → {ABBR[b]} and {ABBR[b]} → {ABBR[c]}, are {d[a][b]} km and "
          f"{d[b][c]} km: the way back home was never taken into account.")
    plot_route(route, title=_route_title("Nearest neighbor", route))
    plt.show()
    return route


# ---------------------------------------------------------------------------
# §4 Sweep
# ---------------------------------------------------------------------------

def angles_table() -> pd.DataFrame:
    """The angle of each city seen from home, in the order of the sweep."""
    order = co.sweep()[1:-1]
    return pd.DataFrame([{"City": ABBR[i], "Angle (degrees)": round(co.angle(i), 1)} for i in order],
                        index=pd.RangeIndex(1, len(order) + 1, name="Order"))


@_light
def sweep() -> list[int]:
    """§4: the order of the sweep, the route and its map."""
    route = co.sweep()
    print("Angle of the line from HH to each city, from north, counterclockwise; the cities are "
          "visited from the smallest angle to the largest:")
    _display(angles_table())
    print(f"Route: {co.label(route)}. Length: {_km(co.length(route))}.")
    plot_route(route, title=_route_title("Sweep", route), rays=True)
    plt.show()
    return route


# ---------------------------------------------------------------------------
# §5 Local search
# ---------------------------------------------------------------------------

def ivanov_table(rows: list[dict]) -> pd.DataFrame:
    """Table of the pass: one row per iteration."""
    return pd.DataFrame([{"Sub-path": co.label(r["sub_path"]), "Before (km)": r["before"],
                          "After the swap (km)": r["after"], "Swap kept": "yes" if r["confirmed"] else ""}
                         for r in rows], index=pd.RangeIndex(1, len(rows) + 1, name="Iteration"))


@_light
def ivanov_pass() -> list[int]:
    """§5: the pass of Ivanov et al. from the route of the nearest neighbor."""
    start = co.nearest_neighbor()
    route, rows = ls.ivanov_pass(start)
    print("For k = 1, ..., 12: the sub-path of the four cities at positions k − 1 to k + 2, before and after "
          "swapping the cities at k and k + 1. The swap is kept if it shortens the sub-path.")
    _display(ivanov_table(rows))
    print(f"Route: {co.label(route)}. Length: {_km(co.length(route))}, "
          f"{_km(co.length(start) - co.length(route))} less than the nearest neighbor.")
    plot_route(route, title=_route_title("After the pass", route))
    plt.show()
    return route


def starting_route(start: str, seed: int = 1) -> list[int]:
    """The route of the form: nearest neighbor, sweep or random (with its seed)."""
    if start == "nearest neighbor":
        return co.nearest_neighbor()
    if start == "sweep":
        return co.sweep()
    if start == "random":
        return co.random_route(seed)
    raise ValueError(f"Unknown starting route {start!r}: the options are {', '.join(STARTS)}.")


def steps_table(steps: list[dict]) -> pd.DataFrame:
    """Table of the search: one row per step."""
    return pd.DataFrame([{"Sub-path reversed": co.label(s["reversed"]) or "— (start)",
                          "Arcs out": "; ".join(map(ls.arc_label, s["out"])) or "—",
                          "Arcs in": "; ".join(map(ls.arc_label, s["in"])) or "—",
                          "Length (km)": s["length"]} for s in steps]).rename_axis("Step")


@_light
def local_search_steps(start: str = "nearest neighbor", move: str = "reversal", seed: int = 1,
                       step_by_step: bool = False) -> list[int]:
    """§5: the local search from the starting route of the form with the move of
    the form. With ``step_by_step``, a map of each step with the arcs out and in."""
    key = _move_key(move)
    route = starting_route(start, seed)
    steps = ls.search(route, key)
    name = STARTS[start] + (f" (seed {seed})" if start == "random" else "")
    print(f"Start: {name}, {co.label(route)}, {_km(co.length(route))}.")
    print(f"Move: {ls.MOVES[key]}, {len(ls.moves(key))} moves in the neighborhood.")
    _display(steps_table(steps))
    end = steps[-1]["route"]
    i, j, delta = ls.best_move(end, key)
    made = len(steps) - 1
    print(f"The search stops after {made} step{'' if made == 1 else 's'} at {co.label(end)}, "
          f"{_km(co.length(end))}: "
          f"a local optimum. The best move from there, reversing {co.label(end[i:j + 1])}, "
          f"gives {_km(co.length(end) + delta)}"
          + (": the same route in the other direction." if (i, j) == (1, len(end) - 2) else "."))
    shortest, _ = _shortest()
    if co.length(end) == shortest:
        print(f"It is as short as the shortest route, {_km(shortest)}.")
    else:
        print(f"The shortest route is {_km(shortest)}: the search stopped "
              f"{_km(co.length(end) - shortest)} above it.")
    if step_by_step:
        for previous, step in zip(steps, steps[1:]):
            plot_route(previous["route"], out=step["out"], new=step["in"],
                       title=f"Step {step['step']}: reverse {co.label(step['reversed'])}, "
                             f"{_km(previous['length'])} → {_km(step['length'])}")
            plt.show()
    plot_route(end, title=_route_title(f"Where the search stops ({ls.MOVES[key]})", end))
    plt.show()
    return end


# ---------------------------------------------------------------------------
# §6 Shortest route and local optima
# ---------------------------------------------------------------------------

def heuristics_table() -> pd.DataFrame:
    """Length of each route of §3-§5 and how far it is above the shortest route."""
    shortest, _ = _shortest()
    nn, sw = co.nearest_neighbor(), co.sweep()
    routes = {"Nearest neighbor": nn, "Sweep": sw,
              "Pass of Ivanov et al. from the nearest neighbor": ls.ivanov_pass(nn)[0],
              "Swap of two adjacent cities from the nearest neighbor": ls.local_optimum(nn, "swap"),
              "Reversal of a sub-path from the nearest neighbor": ls.local_optimum(nn, "reversal"),
              "Reversal of a sub-path from the sweep": ls.local_optimum(sw, "reversal")}
    return pd.DataFrame({name: {"Length (km)": co.length(r), "Above the shortest (%)": round(ex.gap(r, shortest), 1)}
                         for name, r in routes.items()}).T.rename_axis("Route")


@_light
def shortest_route() -> int:
    """§6: the shortest route, how it is calculated, and each heuristic against it."""
    started = time.perf_counter()
    shortest, routes = ex.shortest_routes()
    seconds = time.perf_counter() - started
    different = ex.distinct(routes)
    print(f"Dynamic programming over the 2^{len(CITIES) - 1} = {2 ** (len(CITIES) - 1):,} sets of cities "
          f"({seconds:.2f} s): the shortest route is {_km(shortest)}.")
    print(f"{len(routes)} routes have that length: {len(different)} different round trips, each in both "
          "directions.")
    for r in different:
        print(f"  {co.label(r)}")
    _display(heuristics_table())
    fig, axes = plt.subplots(1, len(different), figsize=(5.2 * len(different), 5.4))
    for k, (ax, r) in enumerate(zip(axes, different), start=1):
        plot_route(r, ax=ax, title=f"Shortest route {k}: {_km(co.length(r))}")
    plt.show()
    return shortest


def optima_table(stops: dict[int, int]) -> pd.DataFrame:
    """Where the search stops: for each length, the starting routes and their share."""
    total = sum(stops.values())
    return pd.DataFrame({"Starting routes": stops,
                         "%": {k: round(100 * v / total, 1) for k, v in stops.items()}}).rename_axis(
        "Length where it stops (km)")


@_light
def local_optima(starts: int = 20000, seed: int = 1, move: str = "reversal") -> pd.DataFrame:
    """§6: the search from ``starts`` random routes, and where it stops."""
    key = _move_key(move)
    started = time.perf_counter()
    stops = ls.random_starts(starts, seed, key)
    seconds = time.perf_counter() - started
    shortest, _ = _shortest()
    table = optima_table(stops)
    print(f"{starts:,} random starting routes (seed {seed}), move: {ls.MOVES[key]} ({seconds:.1f} s).")
    print(f"The search stops at {len(stops)} different lengths; "
          f"{stops.get(shortest, 0):,} starts ({100 * stops.get(shortest, 0) / starts:.1f} %) reach the "
          f"shortest route, {_km(shortest)}.")
    _display(table)
    fig, ax = plt.subplots(figsize=(7, 3.2))
    ax.bar([f"{k:,}" for k in stops], list(stops.values()), color=[IN if k == shortest else ROUTE for k in stops])
    ax.set_xlabel("Length where the search stops (km)")
    ax.set_ylabel("Starting routes")
    ax.tick_params(axis="x", labelsize=8, rotation=45 if len(stops) > 12 else 0)
    ax.spines[["top", "right"]].set_visible(False)
    plt.show()
    return table


# ---------------------------------------------------------------------------
# Maps of the document
# ---------------------------------------------------------------------------

@_light
def document_figures(folder: str | Path = "figures") -> list[Path]:
    """Draw the three maps of traveling_salesman.md as PNG files in ``folder``."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    nn = co.nearest_neighbor()
    end = ls.local_optimum(nn, "reversal")
    figures = {"nearest_neighbor.png": dict(route=nn, title=_route_title("Nearest neighbor", nn)),
               "sweep.png": dict(route=co.sweep(), title=_route_title("Sweep", co.sweep()), rays=True),
               "local_search.png": dict(route=end, title=_route_title(
                   "Reversal of a sub-path from the nearest neighbor", end))}
    paths = []
    for name, options in figures.items():
        fig, ax = plt.subplots(figsize=(5.2, 5.4))
        plot_route(ax=ax, **options)
        fig.tight_layout()
        fig.savefig(folder / name, dpi=150)
        plt.close(fig)
        paths.append(folder / name)
    return paths
