import pytest

from src.interfaces.http_client import HttpError
from src.repositories.task_orchestration.flows.task_downloader import (
    PageContentDownloader,
)
from src.settings import Settings, TableOfContents

from .stubs.stub_http import StubSyncHttpClient
from .stubs.stub_storage import StubStorage


def test_downloader_execute():

    # given
    settings = Settings()
    internal_wiki_page = "Example_Film"
    client = StubSyncHttpClient(
        # Reminder: the flow will call internally `fetch_page_links`
        # thus the response should contain a link to an internal wiki page
        response=f"""
                <html>
                    <a href="./{internal_wiki_page}" class="mw-redirect">Example Film</a>
                </html>
                """
    )
    start_page = TableOfContents(
        page_id="page_id",
        entity_type="Movie",
    )
    storage_handler = StubStorage()
    runner = PageContentDownloader(settings=settings, http_client=client)

    # when
    result = runner.execute(
        start_page,
        storage_handler=storage_handler,
        return_results=True,
    )

    # then
    assert result == [internal_wiki_page]


def test_download_page_return_page_id():

    # given
    settings = Settings()
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


def test_download_page_using_storage_return_content():

    # given
    settings = Settings()
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


def test_download_page_using_storage_dont_return_content():

    # given
    settings = Settings()
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


def test_download_page_http_error():

    # given
    settings = Settings()
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
