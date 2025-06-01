import pytest

from src.interfaces.http_client import HttpError
from src.repositories.flows.task_downloader import DownloaderFlow
from src.settings import Settings, WikiTOCPageConfig

from .stubs.stub_http import StubHttpClient
from .stubs.stub_storage import StubStorage


async def test_execute():

    # given
    settings = Settings()
    internal_wiki_page = "Example_Film"
    client = StubHttpClient(
        # Reminder: the flow will call internally `fetch_page_links`
        # thus the response should contain a link to an internal wiki page
        response=f"""
                <html>
                    <a href="./{internal_wiki_page}" class="mw-redirect">Example Film</a>
                </html>
                """
    )
    start_page = WikiTOCPageConfig(
        page_id="page_id",
        toc_content_type="film",
    )
    storage_handler = StubStorage()
    runner = DownloaderFlow(settings=settings, http_client=client)

    # when
    result = await runner.execute(
        start_page,
        storage_handler=storage_handler,
        return_results=True,
    )

    # then
    assert result == [internal_wiki_page]


async def test_download_page_return_page_id():

    # given
    settings = Settings()
    client = StubHttpClient(response="<html>Test Content</html>")
    runner = DownloaderFlow(settings=settings, http_client=client)
    storage_handler = StubStorage()

    # when
    result = await runner.download_page(
        "page_id",
        storage_handler=storage_handler,
        return_content=False,
    )

    # then
    assert result == "page_id"
    assert storage_handler.is_inserted is True


async def test_download_page_using_storage_return_content():

    # given
    settings = Settings()
    client = StubHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()
    runner = DownloaderFlow(settings=settings, http_client=client)

    # when
    result = await runner.download_page(
        "page_id",
        storage_handler=storage_handler,
        return_content=True,  # return the content
    )

    # then
    assert result == "<html>Test Content</html>"
    assert storage_handler.is_inserted is True


async def test_download_page_using_storage_dont_return_content():

    # given
    settings = Settings()
    client = StubHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()
    runner = DownloaderFlow(settings=settings, http_client=client)

    # when
    page_id = await runner.download_page(
        "page_id",
        storage_handler=storage_handler,
        return_content=False,
    )

    # then
    assert page_id == "page_id"
    assert storage_handler.is_inserted is True


async def test_download_page_http_error():

    # given
    settings = Settings()
    client = StubHttpClient(
        response="<html>Test Content</html>",
        raise_exc=HttpError("Boom", status_code=503),
    )
    runner = DownloaderFlow(settings=settings, http_client=client)

    # when
    with pytest.raises(HttpError) as exc_info:
        await runner.download_page(
            "page_id",
            return_content=True,
        )
    # then
    assert exc_info.value.status_code == 503
    assert "Boom" in str(exc_info.value)
