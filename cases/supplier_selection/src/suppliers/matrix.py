"""Weighted decision matrix for one component (§3).

Each supplier gets a weighted score: the sum of its scores on the criteria
times their weights. With the price as one more criterion, the price score is
10 x (highest price - price) / (highest price - lowest price) among the
suppliers whose offers are compared (by default, all that offer the
component), and the weights of the other criteria are
multiplied by (1 - weight of the price).
"""

from __future__ import annotations

from .data import CRITERIA, PRICE, S, SCORES, WEIGHTS, q


def offering(component: str, suppliers=S) -> list[str]:
    """The suppliers that offer a component, acceptable or not."""
    return [s for s in suppliers if component in PRICE[s]]


def price_scores(component: str, suppliers=S) -> dict:
    """Price score of each of the given suppliers that offers the component
    (points, 0-10). The highest and lowest prices are those of the offers compared."""
    prices = {s: PRICE[s][component] for s in offering(component, suppliers)}
    high, low = max(prices.values()), min(prices.values())
    if high == low:
        raise ValueError("The price score needs at least two offers with different prices.")
    return {s: 10 * (high - p) / (high - low) for s, p in prices.items()}


def with_price(component: str, price_weight: float, suppliers=S) -> dict:
    """Weighted score of each of the given suppliers that offers the component,
    with the price weighing price_weight (0-1) and the other criteria the rest, in
    the same proportions as in the scorecard."""
    if not 0 <= price_weight <= 1:
        raise ValueError("The weight of the price must be between 0 and 1.")
    ps = price_scores(component, suppliers)
    return {s: (1 - price_weight) * q[s] + price_weight * ps[s] for s in ps}


def weights_with_price(price_weight: float) -> dict:
    """The weights of all the criteria when the price weighs price_weight."""
    weights = {k: (1 - price_weight) * WEIGHTS[k] for k in CRITERIA}
    weights["Price"] = price_weight
    return weights


def ranking(scores: dict) -> list[str]:
    """Suppliers from the highest score to the lowest."""
    return sorted(scores, key=lambda s: -scores[s])


def scorecard_row(s: str) -> dict:
    """Scores of a supplier on each criterion and its weighted score."""
    return {**SCORES[s], "Weighted score": q[s]}
