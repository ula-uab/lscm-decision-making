"""Arrival patterns: how the passengers of a flight arrive before departure.

A pattern is a probability function of the arrival time before departure,
measured in 5-minute slots, with its parameters:

- **normal**, with mean ``mu`` and standard deviation ``sigma > 0``;
- **Erlang**, with shape ``alpha`` (an integer greater than 0) and
  ``beta > 0``.

``PATTERNS`` holds the five predefined patterns of the case (lecturer,
05/10/2026). A student can also give a group of flights a normal or an
Erlang function with parameters of his or her own.

The share of the passengers of a flight in each slot ``i = 1, ..., n`` is
the density at ``i`` divided by the sum of the density over the ``n`` slots
(design, §6.1, Equation E.4). Slot 1 is the 5 minutes that end when the gate
closes. The Erlang density uses ``beta`` as a rate (Equation E.2): its mean
is ``alpha / beta``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

FUNCTIONS = ("normal", "erlang")
PARAMETERS = {"normal": ("mu", "sigma"), "erlang": ("alpha", "beta")}


@dataclass(frozen=True)
class ArrivalPattern:
    """A probability function and its two parameters, in 5-minute slots.

    ``name`` is the name of a predefined pattern, or empty for a pattern
    with parameters chosen by the student.
    """
    function: str
    first: float
    second: float
    name: str = ""

    def __post_init__(self):
        if self.function not in FUNCTIONS:
            raise ValueError(f"The function must be one of {FUNCTIONS}, not {self.function!r}")
        if self.function == "normal" and not self.second > 0:
            raise ValueError("The standard deviation σ must be greater than 0")
        if self.function == "erlang":
            if not (float(self.first).is_integer() and self.first > 0):
                raise ValueError("The shape α must be an integer greater than 0")
            if not self.second > 0:
                raise ValueError("β must be greater than 0")

    @property
    def parameters(self) -> dict:
        """The parameters by name: ``{"mu": ..., "sigma": ...}`` or ``{"alpha": ..., "beta": ...}``."""
        first, second = PARAMETERS[self.function]
        alpha = int(self.first) if self.function == "erlang" else self.first
        return {first: alpha, second: self.second}

    def label(self) -> str:
        """Text shown to the student, for example "Long-haul · Erlang, α = 13, β = 0.5"."""
        if self.function == "normal":
            text = f"Normal, μ = {_number(self.first)}, σ = {_number(self.second)}"
        else:
            text = f"Erlang, α = {int(self.first)}, β = {_number(self.second)}"
        return f"{self.name} · {text}" if self.name else text

    def density(self, x) -> np.ndarray:
        """Density of the pattern at ``x`` (slots): Equation E.1 or E.2."""
        x = np.asarray(x, dtype=float)
        if self.function == "normal":
            mu, sigma = self.first, self.second
            return np.exp(-(x - mu) ** 2 / (2 * sigma ** 2)) / (sigma * math.sqrt(2 * math.pi))
        alpha, beta = self.first, self.second
        # In logarithms: x ** (alpha - 1) overflows for large alpha
        log_density = alpha * math.log(beta) - math.lgamma(alpha) + (alpha - 1) * np.log(x) - beta * x
        return np.exp(log_density)

    def shares(self, n: int) -> np.ndarray:
        """Share of the passengers in each slot ``i = 1, ..., n`` (Equation E.4).

        Raises ``ValueError`` if the density is 0 in all the slots, or is not
        a finite number: the shares cannot be computed, and the passengers of
        the flights would be lost."""
        density = self.density(np.arange(1, n + 1))
        total = density.sum()
        if not (np.isfinite(total) and total > 0):
            raise ValueError(f"With the arrival pattern {self.label()}, no passenger arrives in the "
                             f"{n} slots before the gate closes: its density is 0 in all of them. "
                             "Choose other parameters.")
        return density / total

    def to_dict(self) -> dict:
        """Form kept in a scenario file."""
        if self.name:
            return {"name": self.name}
        return {"function": self.function, **self.parameters}

    @classmethod
    def from_dict(cls, data: dict) -> "ArrivalPattern":
        """Inverse of ``to_dict``."""
        if "name" in data:
            if data["name"] not in PATTERNS:
                raise ValueError(f"Unknown arrival pattern {data['name']!r}")
            return PATTERNS[data["name"]]
        function = data.get("function")
        if function not in PARAMETERS:
            raise ValueError(f"Unknown function of an arrival pattern: {function!r}")
        first, second = PARAMETERS[function]
        return cls(function, data[first], data[second])


def normal(mu: float, sigma: float) -> ArrivalPattern:
    """A normal pattern with parameters chosen by the student."""
    return ArrivalPattern("normal", mu, sigma)


def erlang(alpha: int, beta: float) -> ArrivalPattern:
    """An Erlang pattern with parameters chosen by the student."""
    return ArrivalPattern("erlang", alpha, beta)


# The five predefined patterns of the case (lecturer, 05/10/2026)
PATTERNS = {p.name: p for p in [
    ArrivalPattern("normal", 11, 5.5, "Domestic, mixed purpose"),
    ArrivalPattern("erlang", 20, 1, "Medium-haul, mixed purpose"),
    ArrivalPattern("normal", 20, 3, "Medium-haul, mainly work trips"),
    ArrivalPattern("erlang", 13, 0.5, "Long-haul"),
    ArrivalPattern("erlang", 3, 0.5, "Shuttle"),
]}

DEFAULT_PATTERN = PATTERNS["Domestic, mixed purpose"]


def _number(value: float) -> str:
    return f"{value:g}"

