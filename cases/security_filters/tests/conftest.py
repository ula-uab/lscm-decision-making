from pathlib import Path

import pandas as pd
import pytest

from security_filters import read_profiles, read_schedule

REFERENCE = Path(__file__).resolve().parents[1] / "reference"
TEMPLATE = REFERENCE / "ProcesaDatosVuelos-plantilla-original.xls"
INDICATORS = REFERENCE / "indicadores-filtros-parte2.xls"


@pytest.fixture(scope="session")
def schedule():
    return read_schedule()


@pytest.fixture(scope="session")
def profiles():
    return read_profiles()


@pytest.fixture(scope="session")
def hypotheses():
    """Sheet "Hipotesis" of indicadores-filtros-parte2.xls (288 rows)."""
    sheet = pd.read_excel(INDICATORS, sheet_name="Hipotesis", engine="xlrd")
    return sheet.iloc[:288, 1:]


@pytest.fixture(scope="session")
def performance():
    """Sheet "Rendimientos" of indicadores-filtros-parte2.xls (288 rows)."""
    sheet = pd.read_excel(INDICATORS, sheet_name="Rendimientos", header=1, engine="xlrd")
    return sheet.iloc[:288, 1:]
