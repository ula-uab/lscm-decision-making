"""The "observed" presentation curve and forecast errors.

The real arrivals at the filters are not available: the observed curve of
19/07/2008 shipped with the package is **invented** by
``tools/generate_observed.py``, which simulates every passenger with "true"
assumptions that the demand scenarios do not know exactly.

After the day, each scenario is a forecast that can be compared with what
was observed, with the same measures used for demand forecasts in the course:

    error = observed - forecast
    MAE   = mean of |error|
    MAPE  = mean of |error| / observed
    bias  = mean of error (positive: the forecast fell short)
"""

from __future__ import annotations

from importlib import resources

import numpy as np
import pandas as pd

from .arrivals import hourly

AVAILABLE_DAYS = ("2008-07-19",)


def read_observed(day: str = "2008-07-19") -> pd.Series:
    """Observed (invented) passengers arriving at the filters per 5-minute slot."""
    if day not in AVAILABLE_DAYS:
        raise ValueError(f"There is an observed curve only for {AVAILABLE_DAYS}")
    path = resources.files("security_filters") / "data" / f"observed_arrivals_{day}.csv"
    with resources.as_file(path) as file:
        observed = pd.read_csv(file, index_col="time")["arrivals"]
    return observed.rename("observed")


def forecast_errors(forecast: pd.Series, observed: pd.Series, by: str = "hour") -> pd.Series:
    """MAE, MAPE and bias of a forecast curve against the observed one.

    ``by="hour"`` compares hourly totals; ``by="slot"`` compares 5-minute
    slots. MAPE only uses the periods with observed passengers.
    """
    if by == "hour":
        forecast, observed = hourly(forecast), hourly(observed)
    elif by != "slot":
        raise ValueError("by must be 'hour' or 'slot'")
    error = observed.to_numpy() - forecast.to_numpy()
    busy = observed.to_numpy() > 0
    return pd.Series({
        "MAE": np.abs(error).mean(),
        "MAPE": np.abs(error[busy] / observed.to_numpy()[busy]).mean(),
        "bias": error.mean(),
        "max_abs_error": np.abs(error).max(),
        "total_forecast": forecast.sum(),
        "total_observed": observed.sum(),
    })


def compare_forecasts(curves: pd.DataFrame, observed: pd.Series, by: str = "hour") -> pd.DataFrame:
    """Forecast errors of several scenario curves, one row per scenario."""
    return pd.DataFrame({name: forecast_errors(curves[name], observed, by)
                         for name in curves}).T
