"""Arrival profiles defined by parameters.

A profile gives the fraction of the passengers of a flight that arrive at the
filters in each 5-minute interval before departure (interval 1 is the 5
minutes just before departure). Here a profile is built from two numbers that
are easy to discuss: the **mean** time before departure at which passengers
arrive and its **standard deviation**, both in minutes.

The arrival time before departure follows a gamma distribution (the
continuous version of the Erlang distribution of the original workbook) with
that mean and standard deviation. Its probability in each interval is the
fraction of the profile. The distribution is cut at the horizon of the
profile (4 hours by default) and the fractions are scaled to add up to 1.

The presets describe typical behaviours by type of flight. **Their values are
provisional**: they are reasonable orders of magnitude, not measured data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .profiles import read_profiles
from .schedule import SLOT_MINUTES

DEFAULT_HORIZON_MIN = 240  # 4 hours = 48 intervals of 5 minutes


@dataclass(frozen=True)
class ArrivalPattern:
    """Mean and standard deviation (minutes before departure) of the arrivals."""
    mean_min: float
    sd_min: float
    description: str = ""


# Provisional values, to be validated by the lecturer
PRESETS = {
    "business": ArrivalPattern(55, 18, "Business destinations: late and punctual arrivals"),
    "leisure": ArrivalPattern(100, 30, "Holiday and charter flights"),
    "low_cost": ArrivalPattern(85, 25, "Low-cost carriers: online check-in, hand luggage"),
    "long_haul": ArrivalPattern(150, 40, "Long-haul and intercontinental flights"),
    "wave": ArrivalPattern(95, 6, "Passengers brought together by bus (tour operator, cruise)"),
}


def gamma_profile(mean_min: float, sd_min: float,
                  horizon_min: int = DEFAULT_HORIZON_MIN) -> np.ndarray:
    """Fractions of a gamma-distributed arrival time, per 5-minute interval."""
    if mean_min <= 0 or sd_min <= 0:
        raise ValueError("The mean and the standard deviation must be positive")
    shape = (mean_min / sd_min) ** 2
    scale = sd_min ** 2 / mean_min
    # Integrate the density on a fine grid (0.1 minutes) interval by interval
    step = 0.1
    t = np.arange(step / 2, horizon_min, step)
    log_density = ((shape - 1) * np.log(t) - t / scale
                   - math.lgamma(shape) - shape * math.log(scale))
    mass = np.exp(log_density) * step
    per_interval = mass.reshape(-1, int(round(SLOT_MINUTES / step))).sum(axis=1)
    return per_interval / per_interval.sum()


def profile_library(patterns: dict[str, ArrivalPattern] | None = None,
                    horizon_min: int = DEFAULT_HORIZON_MIN,
                    include_original: bool = True) -> pd.DataFrame:
    """Table of profiles: the presets (or ``patterns``) and, if
    ``include_original``, the five profiles of the original workbook.

    All profiles share the same horizon; the original ones (29 intervals)
    are completed with zeros.
    """
    patterns = PRESETS if patterns is None else patterns
    n = horizon_min // SLOT_MINUTES
    index = pd.RangeIndex(1, n + 1, name="interval_before_departure")
    table = pd.DataFrame({name: gamma_profile(p.mean_min, p.sd_min, horizon_min)
                          for name, p in patterns.items()}, index=index)
    if include_original:
        original = read_profiles().reindex(index, fill_value=0.0)
        table = pd.concat([table, original], axis=1)
    return table


def describe(profiles: pd.DataFrame) -> pd.DataFrame:
    """Mean, standard deviation and peak (minutes before departure) of each profile."""
    minutes = (profiles.index.to_numpy() - 0.5) * SLOT_MINUTES
    rows = {}
    for name in profiles:
        f = profiles[name].to_numpy()
        mean = (f * minutes).sum()
        rows[name] = {
            "mean_min": mean,
            "sd_min": math.sqrt((f * (minutes - mean) ** 2).sum()),
            "peak_min": minutes[f.argmax()],
        }
    return pd.DataFrame(rows).T
