"""Plots of presentation curves and scenario results."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .schedule import SLOT_MINUTES


def _hour_axis(ax, n_slots: int) -> None:
    slots_per_hour = 60 // SLOT_MINUTES
    ticks = np.arange(0, n_slots + 1, 2 * slots_per_hour)
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t // slots_per_hour:02d}:00" for t in ticks])
    ax.set_xlim(0, n_slots)
    ax.set_xlabel("Time of day")
    ax.grid(alpha=0.3)


def plot_curves(curves: dict[str, pd.Series] | pd.Series, ax=None,
                title: str = "Passengers arriving at the security filters"):
    """One or several presentation curves on the same axes."""
    if isinstance(curves, pd.Series):
        curves = {curves.name or "arrivals": curves}
    ax = ax or plt.subplots(figsize=(11, 4))[1]
    for label, curve in curves.items():
        ax.step(np.arange(len(curve)), curve.to_numpy(), where="post", label=label)
    _hour_axis(ax, len(next(iter(curves.values()))))
    ax.set_ylabel(f"Passengers per {SLOT_MINUTES} min")
    ax.set_title(title)
    ax.legend()
    return ax


def plot_scenario(result: pd.DataFrame, title: str = "", ax=None):
    """Arrivals, capacity and queue of one scenario."""
    ax = ax or plt.subplots(figsize=(11, 4))[1]
    x = np.arange(len(result))
    ax.bar(x, result["arrivals"], width=1.0, align="edge", alpha=0.5, label="Arrivals")
    ax.step(x, result["capacity"], where="post", color="black", label="Capacity")
    ax.plot(x + 1, result["queue"], color="tab:red", label="Queue (end of slot)")
    _hour_axis(ax, len(result))
    ax.set_ylabel(f"Passengers per {SLOT_MINUTES} min")
    ax.set_title(title)
    ax.legend()
    return ax
