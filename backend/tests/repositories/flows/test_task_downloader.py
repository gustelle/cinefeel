import pytest

from src.interfaces.http_client import HttpError
from src.repositories.orchestration.tasks.task_downloader import PageContentDownloader
from src.settings import Settings

from .stubs.stub_http import StubSyncHttpClient
from .stubs.stub_storage import StubStorage


def test_download_page_return_page_id(
    test_settings: Settings,
):

    # given

    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    runner = PageContentDownloader(settings=settings, http_client=client)
    storage_handler = StubStorage()

    # when
    result = runner.download(
        "page_id",
        storage_handler=storage_handler,
        return_content=False,
    )

    # then
    assert result == "page_id"
    assert storage_handler.is_inserted is True


def test_download_page_using_storage_return_content(test_settings: Settings):

    # given
    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()
    runner = PageContentDownloader(settings=settings, http_client=client)

    # when
    result = runner.download(
        "page_id",
        storage_handler=storage_handler,
        return_content=True,  # return the content
    )

    # then
    assert result == "<html>Test Content</html>"
    assert storage_handler.is_inserted is True


def test_download_page_using_storage_dont_return_content(test_settings: Settings):

    # given

    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()
    runner = PageContentDownloader(settings=settings, http_client=client)

    # when
    page_id = runner.download(
        "page_id",
        storage_handler=storage_handler,
        return_content=False,
    )

    # then
    assert page_id == "page_id"
    assert storage_handler.is_inserted is True


def test_download_page_http_error(test_settings: Settings):

    # given

    settings = test_settings
    client = StubSyncHttpClient(
        response="<html>Test Content</html>",
        raise_exc=HttpError("Boom", status_code=503),
    )
    runner = PageContentDownloader(settings=settings, http_client=client)

    # when
    with pytest.raises(HttpError) as exc_info:
        runner.download(
            "page_id",
            return_content=True,
        )
    # then
    assert exc_info.value.status_code == 503
    assert "Boom" in str(exc_info.value)
