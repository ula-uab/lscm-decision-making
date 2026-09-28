"""Arrival profiles: how the passengers of a flight arrive at the filters.

A profile gives, for each 5-minute interval before departure, the fraction of
the passengers of a flight that arrive at the security filters in that
interval. Interval 1 is the 5 minutes just before departure, interval 2 the
5 minutes before that one, and so on. The fractions of a profile add up to 1.

The five profiles of the original case (sheet "Distribuciones" of
``ProcesaDatosVuelos-plantilla-original.xls``) are stored in
``data/arrival_profiles.csv``. The original workbook only keeps the
fractions, not the parameters of the distributions they come from.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

import pandas as pd

# Names in the original workbook and names used in this package
LEGACY_NAMES = {
    "DistribucionGaus": "gauss",
    "DistribucionErlang": "erlang",
    "DistribucionNormal2": "normal2",
    "DistribucionErlang2": "erlang2",
    "DistribucionErlang3": "erlang3",
}


def default_profiles_path() -> Path:
    """Path of the arrival profiles shipped with the package."""
    return Path(str(resources.files("security_filters") / "data" / "arrival_profiles.csv"))


def read_profiles(path: str | Path | None = None) -> pd.DataFrame:
    """Read the arrival profiles.

    Returns a table with one column per profile and one row per 5-minute
    interval before departure (index ``interval_before_departure``, from 1).
    """
    path = default_profiles_path() if path is None else Path(path)
    profiles = pd.read_csv(path, index_col="interval_before_departure")
    check_profiles(profiles)
    return profiles


def read_profiles_from_workbook(path: str | Path) -> pd.DataFrame:
    """Read the profiles from the sheet "Distribuciones" of the original workbook.

    Used once to build ``arrival_profiles.csv`` and by the tests to check it.
    """
    raw = pd.read_excel(path, sheet_name="Distribuciones", header=0, engine="xlrd")
    raw = raw.iloc[1:30]  # the row under the names is empty; then 29 intervals
    profiles = raw.rename(columns=LEGACY_NAMES)[list(LEGACY_NAMES.values())]
    profiles.index = pd.RangeIndex(1, len(profiles) + 1, name="interval_before_departure")
    return profiles.astype(float)


def check_profiles(profiles: pd.DataFrame, tolerance: float = 1e-6) -> None:
    """Raise ValueError if a profile has negative values or does not add up to 1."""
    if (profiles < 0).any().any():
        raise ValueError("A profile has negative fractions")
    totals = profiles.sum()
    wrong = totals[(totals - 1).abs() > tolerance]
    if not wrong.empty:
        raise ValueError(f"These profiles do not add up to 1: {wrong.to_dict()}")
