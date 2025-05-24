import pytest
from prefect.testing.utilities import prefect_test_harness

from src.interfaces.http_client import HttpError
from src.repositories.flows.task_downloader import download_page
from src.settings import Settings

from .stubs.stub_http import StubHttpClient
from .stubs.stub_storage import StubStorage


async def test_download_page_return_content():

    # given
    settings = Settings()
    client = StubHttpClient(response="<html>Test Content</html>")

    # when
    with prefect_test_harness():
        result = await download_page(
            "page_id",
            settings=settings,
            http_client=client,
            return_content=True,
        )

    # then
    assert result == "<html>Test Content</html>"


async def test_download_page_return_page_id():

    # given
    settings = Settings()
    client = StubHttpClient(response="<html>Test Content</html>")

    # when
    with prefect_test_harness():
        result = await download_page(
            "page_id",
            settings=settings,
            http_client=client,
            return_content=False,
        )

    # then
    assert result == "page_id"


async def test_download_page_using_storage():

    # given
    settings = Settings()
    client = StubHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()

    # when
    with prefect_test_harness():
        await download_page(
            "page_id",
            settings=settings,
            http_client=client,
            storage_handler=storage_handler,
            return_content=True,
        )

    # then
    assert storage_handler.is_inserted is True


async def test_download_page_http_error():

    # given
    settings = Settings()
    client = StubHttpClient(
        response="<html>Test Content</html>",
        raise_exc=HttpError("Boom", status_code=503),
    )

    # when
    with prefect_test_harness():
        with pytest.raises(HttpError) as exc_info:

            await download_page(
                "page_id",
                settings=settings,
                http_client=client,
                return_content=True,
            )
    # then
    assert exc_info.value.status_code == 503
    assert "Boom" in str(exc_info.value)
