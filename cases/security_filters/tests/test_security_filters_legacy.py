"""The faithful reproduction gives the numbers of the original workbooks."""

import numpy as np

from security_filters import flights_of_day
from security_filters.legacy import legacy_performance, legacy_presentation_curve


def test_macro_curve_of_19_july_2008_matches_workbook(schedule, profiles, hypotheses):
    """Column "Pax-sc1" of the sheet "Hipotesis" is the curve of the macro for
    19/07/2008 with the Erlang profile and all seats occupied."""
    flights = flights_of_day(schedule, "2008-07-19")
    curve = legacy_presentation_curve(flights, profiles, profile="erlang")
    np.testing.assert_array_equal(curve.to_numpy(), hypotheses["Pax-sc1"].to_numpy())
    assert curve.sum() == 74631


def test_rendimientos_sheet_is_reproduced(performance):
    result = legacy_performance(performance["Presentación"], performance["Capacidad Filtros"])
    np.testing.assert_allclose(result["queue"], performance["Colas"])
    np.testing.assert_allclose(result["idle"], performance["Ociosidad"])


def test_capacity_of_the_workbook_is_fraction_of_500(hypotheses, performance):
    np.testing.assert_allclose(hypotheses["Capacidad Filtros"] * 500,
                               performance["Capacidad Filtros"])
