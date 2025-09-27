import pytest

from src.entities.content import PageLink, TableOfContents
from src.interfaces.http_client import HttpError
from src.repositories.orchestration.tasks.task_downloader import ContentDownloaderTask
from src.settings import Settings

from .stubs.stub_http import StubSyncHttpClient
from .stubs.stub_parser import StubContentParser
from .stubs.stub_storage import StubStorage


def test_download_return_page_id(
    test_settings: Settings,
):

    # given
    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    runner = ContentDownloaderTask(settings=settings, http_client=client)
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


def test_download_return_content(test_settings: Settings):

    # given
    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()
    runner = ContentDownloaderTask(settings=settings, http_client=client)

    # when
    result = runner.download(
        "page_id",
        storage_handler=storage_handler,
        return_content=True,  # return the content
    )

    # then
    assert result == "<html>Test Content</html>"
    assert storage_handler.is_inserted is True


def test_download_page_using_storage(test_settings: Settings):

    # given

    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()
    runner = ContentDownloaderTask(settings=settings, http_client=client)

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

    settings = test_settings
    client = StubSyncHttpClient(
        raise_exc=HttpError("Boom", status_code=503),
    )

    runner = ContentDownloaderTask(settings=settings, http_client=client)

    # when
    with pytest.raises(HttpError) as exc_info:
        runner.download(
            "page_id",
            return_content=True,
        )

    # then
    assert exc_info.value.status_code == 503
    assert "Boom" in str(exc_info.value)


def test_extract_page_links(test_settings: Settings, mocker):
    # given
    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    runner = ContentDownloaderTask(settings=settings, http_client=client)
    extractor = StubContentParser(
        inner_links=[
            PageLink(page_id="link1", entity_type="Movie"),
            PageLink(page_id="link2", entity_type="Movie"),
        ]
    )

    # when
    result = runner.extract_page_links(
        config=TableOfContents(page_id="page_id", entity_type="Movie"),
        link_extractor=extractor,
    )

    # then
    assert extractor._is_called is True
    assert result == [
        PageLink(page_id="link1", entity_type="Movie"),
        PageLink(page_id="link2", entity_type="Movie"),
    ]


def test_execute_with_TableOfContents(test_settings: Settings):
    """when the task is executed with a TableOfContents, it should extract the links and download each linked page."""

    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    runner = ContentDownloaderTask(settings=settings, http_client=client)
    storage_handler = StubStorage()
    extractor = StubContentParser(
        inner_links=[
            PageLink(page_id="link1", entity_type="Movie"),
            PageLink(page_id="link2", entity_type="Movie"),
        ]
    )

    toc = TableOfContents(page_id="toc_id", entity_type="Movie")
    # imagine this TOC contains 2 links: link1 and link2

    # when
    result = runner.execute(
        page=toc,
        storage_handler=storage_handler,
        link_extractor=extractor,
        return_results=True,
    )

    # then
    assert extractor._is_called is True
    assert result == ["link1", "link2"]
    assert storage_handler.is_inserted is True


def test_execute_with_PageLink(test_settings: Settings):
    """when the task is executed with a PageLink, it should download the page content."""

    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    runner = ContentDownloaderTask(settings=settings, http_client=client)
    storage_handler = StubStorage()

    page_link = PageLink(page_id="link1", entity_type="Movie")

    # when
    result = runner.execute(
        page=page_link,
        storage_handler=storage_handler,
        return_results=True,
    )

    # then
    assert result == ["link1"]
    assert storage_handler.is_inserted is True


def test_execute_return_results(test_settings: Settings):
    """when the task is executed with a TableOfContents, it should extract the links and download each linked page."""

    settings = test_settings
    client = StubSyncHttpClient(response="<html>Test Content</html>")
    runner = ContentDownloaderTask(settings=settings, http_client=client)
    storage_handler = StubStorage()

    page_link = PageLink(page_id="link1", entity_type="Movie")

    # when
    runner.execute(
        page=page_link,
        storage_handler=storage_handler,
        return_results=True,
    )

    # then
    assert storage_handler.is_inserted is True


# def test_execute_return_no_results(test_settings: Settings):
#     pass
