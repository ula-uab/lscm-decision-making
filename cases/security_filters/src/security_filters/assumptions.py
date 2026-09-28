"""Assumptions on the flights of a day, written as simple rules.

In the original workbook the assumptions were typed flight by flight in the
sheet "Paso2": load factor, time correction and arrival profile. Here they
are written as a short list of **rules**. Each rule says which flights it
applies to and which values it sets:

    rules = [
        {"load_factor": 0.85, "profile": "leisure"},              # every flight
        {"airline": "AEA", "load_factor": 0.80, "transfer_share": 0.30},
        {"destination": ["MAD", "BCN"], "profile": "business"},
        {"airline": "TOM", "advance_min": 30, "profile": "wave"},
        {"flight": "TOM1796", "advance_min": 45},                  # one flight
    ]

Rules are applied in order: when several rules match a flight, the last one
wins for each value it sets. Write them from the most general to the most
specific.

Which flights (all conditions of a rule must hold; a list means "any of"):

- ``airline``: ICAO code of the airline, the first three letters of the
  flight number (``"TOM"``);
- ``destination``: IATA code of the destination airport (``"LGW"``);
- ``flight``: flight number (``"TOM1796"``);
- ``departure_from`` and ``departure_to``: departure time window,
  ``"HH:MM"``, from included to excluded.

Which values:

- ``load_factor``: fraction of the seats that are occupied (0 to 1);
- ``transfer_share``: fraction of the passengers who connect to another
  flight and do not go through the security filters (0 to 1);
- ``advance_min``: minutes by which the passengers arrive earlier than the
  profile says, for example because a bus brings them all together
  (negative values delay them);
- ``profile``: name of the arrival profile (see ``distributions``).

The passengers who go through the filters are
``seats * load_factor * (1 - transfer_share)``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CONDITIONS = ("airline", "destination", "flight", "departure_from", "departure_to")
VALUES = ("load_factor", "transfer_share", "advance_min", "profile")
DEFAULTS = {"load_factor": 1.0, "transfer_share": 0.0, "advance_min": 0, "profile": "erlang"}


def apply_rules(flights: pd.DataFrame, rules: list[dict],
                defaults: dict | None = None) -> pd.DataFrame:
    """Table of assumptions, one row per flight (the new "Paso2").

    Adds to ``flights`` the columns ``load_factor``, ``transfer_share``,
    ``advance_min``, ``profile``, ``passengers`` (who go through the
    filters) and ``rules`` (numbers of the rules that matched, from 1).
    """
    values = dict(DEFAULTS, **(defaults or {}))
    table = flights.copy()
    for column, value in values.items():
        table[column] = value
    table["rules"] = ""

    for number, rule in enumerate(rules, start=1):
        _check_rule(rule, number)
        match = _matches(table, rule)
        for column in VALUES:
            if column in rule:
                table.loc[match, column] = rule[column]
        table.loc[match, "rules"] = (table.loc[match, "rules"] + f" {number}").str.strip()

    _check_values(table)
    table["passengers"] = table["seats"] * table["load_factor"] * (1 - table["transfer_share"])
    return table


def read_rules(path: str | Path) -> list[dict]:
    """Read rules from a CSV or Excel file with one rule per row.

    Columns are the condition and value names above; empty cells are
    ignored. Several codes in one cell (``"MAD BCN"`` or ``"MAD, BCN"``)
    mean "any of".
    """
    path = Path(path)
    table = pd.read_excel(path) if path.suffix.lower() in (".xls", ".xlsx") else pd.read_csv(path)
    rules = []
    for _, row in table.iterrows():
        rule = {}
        for column, value in row.items():
            if pd.isna(value) or column not in CONDITIONS + VALUES:
                continue
            if column in ("airline", "destination", "flight"):
                codes = str(value).replace(",", " ").split()
                value = codes if len(codes) > 1 else codes[0]
            rule[column] = value
        rules.append(rule)
    return rules


def summary_by_airline(table: pd.DataFrame) -> pd.DataFrame:
    """Flights, seats and passengers through the filters by airline."""
    return (table.groupby("airline")
            .agg(flights=("flight", "size"), seats=("seats", "sum"),
                 passengers=("passengers", "sum"))
            .sort_values("seats", ascending=False))


def _matches(table: pd.DataFrame, rule: dict) -> pd.Series:
    match = pd.Series(True, index=table.index)
    for column in ("airline", "destination", "flight"):
        if column in rule:
            wanted = rule[column] if isinstance(rule[column], (list, tuple, set)) else [rule[column]]
            match &= table[column].isin([str(w).strip() for w in wanted])
    if "departure_from" in rule:
        match &= table["departure_minute"] >= _minutes(rule["departure_from"])
    if "departure_to" in rule:
        match &= table["departure_minute"] < _minutes(rule["departure_to"])
    return match


def _check_rule(rule: dict, number: int) -> None:
    unknown = set(rule) - set(CONDITIONS) - set(VALUES)
    if unknown:
        raise ValueError(f"Rule {number}: unknown keys {sorted(unknown)}. "
                         f"Conditions: {CONDITIONS}. Values: {VALUES}")


def _check_values(table: pd.DataFrame) -> None:
    for column in ("load_factor", "transfer_share"):
        wrong = table[(table[column] < 0) | (table[column] > 1)]
        if not wrong.empty:
            raise ValueError(f"{column} must be between 0 and 1 "
                             f"(flights {wrong['flight'].head().tolist()})")


def _minutes(text: str) -> int:
    hours, minutes = str(text).split(":")
    return int(hours) * 60 + int(minutes)
