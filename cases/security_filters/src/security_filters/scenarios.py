"""Demand scenarios: sets of assumptions that give a presentation curve.

A demand scenario is a name and a list of rules (see ``assumptions``). Each
scenario gives one presentation curve for the same flights, so the curves of
several scenarios describe what the demand at the filters could be. The
policies of ``policies`` are then evaluated on those curves.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .arrivals import presentation_curve
from .assumptions import apply_rules


@dataclass
class DemandScenario:
    """A named set of assumptions on the flights."""
    name: str
    rules: list[dict] = field(default_factory=list)
    description: str = ""

    def assumptions(self, flights: pd.DataFrame) -> pd.DataFrame:
        """Table of assumptions, one row per flight."""
        return apply_rules(flights, self.rules)

    def curve(self, flights: pd.DataFrame, profiles: pd.DataFrame) -> pd.Series:
        """Presentation curve of the scenario."""
        return presentation_curve(self.assumptions(flights), profiles).rename(self.name)


def demand_curves(scenarios: list[DemandScenario], flights: pd.DataFrame,
                  profiles: pd.DataFrame) -> pd.DataFrame:
    """Presentation curves of several scenarios, one column per scenario."""
    _check_unique([s.name for s in scenarios], "scenario")
    return pd.concat([s.curve(flights, profiles) for s in scenarios], axis=1)


def _check_unique(names: list[str], what: str) -> None:
    repeated = sorted({n for n in names if names.count(n) > 1})
    if repeated:
        raise ValueError(f"Each {what} needs its own name; repeated: {repeated}")
