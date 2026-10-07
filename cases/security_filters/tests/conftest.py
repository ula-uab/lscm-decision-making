import pytest

from security_filters import read_schedule


@pytest.fixture(scope="session")
def schedule():
    return read_schedule()
