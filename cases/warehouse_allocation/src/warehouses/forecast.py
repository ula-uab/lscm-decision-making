"""Forecast of the orders of C3 with a 4-week moving average, and its error (§6)."""

from __future__ import annotations

from .data import orders_C3

WINDOW = 4


def moving_average(orders: list[float] = orders_C3, window: int = WINDOW) -> list[float | None]:
    """Forecast of each week: the average of the orders of the previous weeks."""
    return [None if week < window else sum(orders[week - window:week]) / window
            for week in range(len(orders))]


def errors(orders: list[float] = orders_C3, window: int = WINDOW) -> list[float | None]:
    """Error of each week: orders - forecast."""
    return [None if f is None else o - f for o, f in zip(orders, moving_average(orders, window))]


def accuracy(orders: list[float] = orders_C3, window: int = WINDOW) -> dict:
    """MAE (pallets/week), MAPE (%) and bias (pallets/week) over the weeks with a forecast."""
    pairs = [(o, e) for o, e in zip(orders, errors(orders, window)) if e is not None]
    n = len(pairs)
    return {
        "MAE": sum(abs(e) for _, e in pairs) / n,
        "MAPE": 100 * sum(abs(e) / o for o, e in pairs) / n,
        "bias": sum(e for _, e in pairs) / n,
    }


def next_week(orders: list[float] = orders_C3, window: int = WINDOW) -> float:
    """Forecast for the week after the last one."""
    return sum(orders[-window:]) / window
