import pytest
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="session", autouse=True)
def prefect_harness():
    """
    Create a per-session Prefect test harness, otherwise it's too slow.
    @see: https://github.com/PrefectHQ/prefect/issues/5693
    """
    with prefect_test_harness():
        yield
