from time import sleep

from prefect import flow, get_run_logger, task
from prefect.futures import wait
from prefect.testing.utilities import prefect_test_harness

from src.entities.film import Film
from src.repositories.flows.task_analyzer import do_storage

from .stubs.stub_storage import StubStorage


def test_do_storage():

    # given
    stub_storage = StubStorage()

    @task
    def fake_analysis() -> Film | None:
        """
        Submit tasks to the executor with a specified concurrency level.
        """
        sleep(5)
        get_run_logger().info("Slept for 5 second")
        return Film(title="Test Film", woa_id="test_woa_id")

    @flow
    def fake_flow():
        """
        A fake flow to test the task analyzer.
        """
        analysis_fut = fake_analysis.submit()
        storage_fut = do_storage.submit(stub_storage, analysis_fut)
        wait([storage_fut])

    # when
    with prefect_test_harness():
        fake_flow()

    # then
    assert stub_storage.is_inserted, "Film was not inserted into the storage."
