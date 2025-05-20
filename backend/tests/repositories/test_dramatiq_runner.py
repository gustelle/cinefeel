import pytest

from src.repositories.dramatiq_downloader import DramatiqDownloader
from src.settings import Settings


@pytest.mark.asyncio
async def test_submit_task():
    """
    Test the submit_task method of the DramatiqRunner class.
    """

    what_to_say = "Hello, World!"

    runner = DramatiqDownloader(settings=Settings())

    # when
    result = await runner.submit(
        what_to_say,
    )

    print(f"Result: {result}")
    # wait for the task to be processed

    val = await runner.run()

    print(f"Val: {val}")
    # Assert that the task was submitted to the broker
