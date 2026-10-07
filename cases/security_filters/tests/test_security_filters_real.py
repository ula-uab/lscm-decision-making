"""Real PPPs in the public package: the 16 days, 288 whole and non-negative
values each, and nothing else (no rules, no values of the flights)."""

import pandas as pd
import pytest

import security_filters as sf

DAYS = [d.date().isoformat() for d in pd.date_range("2008-07-16", "2008-07-31")]


def test_the_file_has_the_16_days_and_only_the_ppps():
    table = sf.read_real_ppps()
    assert list(table.columns) == DAYS
    assert list(table.index) == list(sf.slot_labels())
    assert (table.dtypes == "int64").all()
    assert (table >= 0).all().all()


def test_real_ppp_of_a_day():
    ppp = sf.real_ppp("2008-07-19")
    assert len(ppp) == 288 and ppp.index[0] == "00:00"
    with pytest.raises(ValueError, match="no real PPP"):
        sf.real_ppp("2008-08-01")
