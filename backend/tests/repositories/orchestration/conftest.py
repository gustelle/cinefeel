import pytest
from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import GlobalConcurrencyLimitCreate
from prefect.logging import disable_run_logger
from prefect.testing.utilities import prefect_test_harness


@pytest.fixture(scope="function", autouse=True)
def disable_task_caching(monkeypatch):
    """Clear Prefect flows between tests to avoid state leakage."""
    monkeypatch.setenv("PREFECT_TASKS_REFRESH_CACHE", "true")
    yield
    monkeypatch.undo()


@pytest.fixture(scope="session", autouse=True)
async def prefect_harness():
    """
    Create a per-session Prefect test harness, otherwise it's too slow.
    @see: https://github.com/PrefectHQ/prefect/issues/5693
    """

    with prefect_test_harness():

        gcl_resource = GlobalConcurrencyLimitCreate(
            name="resource-rate-limiting",
            limit=1,
            active=True,
            active_slots=1,
            slot_decay_per_second=1,
        )
        gcl_api = GlobalConcurrencyLimitCreate(
            name="api-rate-limiting",
            limit=1,
            active=True,
            active_slots=1,
            slot_decay_per_second=1,
        )

        async with get_client() as client:
            await client.create_global_concurrency_limit(concurrency_limit=gcl_resource)
            await client.create_global_concurrency_limit(concurrency_limit=gcl_api)
            print("Created GCLs for the test session")

        print("Prefect test harness started for the session.")
        with disable_run_logger():
            yield
