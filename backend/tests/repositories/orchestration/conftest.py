import pytest
from prefect.logging import disable_run_logger
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="function", autouse=True)
def disable_task_caching(monkeypatch):
    """Clear Prefect flows between tests to avoid state leakage."""
    monkeypatch.setenv("PREFECT_TASKS_REFRESH_CACHE", "true")
    yield
    monkeypatch.undo()


@pytest.fixture(scope="session", autouse=True)
def prefect_harness():
    """
    Create a per-session Prefect test harness, otherwise it's too slow.
    @see: https://github.com/PrefectHQ/prefect/issues/5693
    """

    with prefect_test_harness():
        print("Prefect test harness started for the session.")
        with disable_run_logger():
            yield
