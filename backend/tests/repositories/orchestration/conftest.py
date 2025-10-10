import pytest
from prefect import flow
from prefect.logging import disable_run_logger
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="session", autouse=True)
def prefect_harness():
    """
    Create a per-session Prefect test harness, otherwise it's too slow.
    @see: https://github.com/PrefectHQ/prefect/issues/5693
    """

    with prefect_test_harness():
        with disable_run_logger():
            yield


@pytest.fixture(scope="function")
def test_flow(prefect_harness):

    yield flow(
        name="test_flow",
    )()
