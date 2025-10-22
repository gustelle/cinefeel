import pytest

from src.entities.content import PageLink, TableOfContents
from src.exceptions import HttpError
from src.repositories.orchestration.tasks.task_scraper import (
    download_and_store,
    execute_task,
    extract_page_links,
)
from src.settings import Settings

from ..stubs.stub_http import StubSyncHttpClient
from ..stubs.stub_parser import StubContentParser
from ..stubs.stub_storage import StubStorage


def test_downloader_task_download_return_page_id(test_settings: Settings):

    # given

    client = StubSyncHttpClient(response="<html>Test Content</html>")

    storage_handler = StubStorage()

    # when
    result = download_and_store(
        http_client=client,
        page_id="page_id",
        settings=test_settings,
        storage_handler=storage_handler,
        return_content=False,
    )

    # then
    assert result == "page_id"
    assert storage_handler.is_inserted is True


def test_downloader_task_download_return_content(test_settings: Settings):

    # given

    client = StubSyncHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()

    # when
    result = download_and_store(
        http_client=client,
        page_id="page_id",
        settings=test_settings,
        storage_handler=storage_handler,
        return_content=True,  # return the content
    )

    # then
    assert result == "<html>Test Content</html>"
    assert storage_handler.is_inserted is True


def test_downloader_task_download_and_store(test_settings: Settings):

    # given

    client = StubSyncHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()

    # when
    page_id = download_and_store(
        http_client=client,
        page_id="page_id",
        settings=test_settings,
        storage_handler=storage_handler,
        return_content=False,
    )

    # then
    assert page_id == "page_id"
    assert storage_handler.is_inserted is True


def test_downloader_task_download_and_store_http_error(test_settings: Settings):

    # given
    client = StubSyncHttpClient(
        raise_exc=HttpError("Boom", status_code=503),
    )
    storage_handler = StubStorage()

    # when
    with pytest.raises(HttpError) as exc_info:
        download_and_store(
            http_client=client,
            page_id="page_id",
            return_content=True,
            settings=test_settings,
            storage_handler=storage_handler,
        )

    # then
    assert exc_info.value.status_code == 503
    assert "Boom" in str(exc_info.value)


def test_downloader_task_extract_page_links(test_settings: Settings):

    # given

    client = StubSyncHttpClient(response="<html>Test Content</html>")

    extractor = StubContentParser(
        inner_links=[
            PageLink(page_id="link1", entity_type="Movie"),
            PageLink(page_id="link2", entity_type="Movie"),
        ]
    )

    # when
    result = extract_page_links(
        http_client=client,
        config=TableOfContents(page_id="page_id", entity_type="Movie"),
        link_extractor=extractor,
        settings=test_settings,
    )

    # then
    assert extractor._is_called is True
    assert result == [
        PageLink(page_id="link1", entity_type="Movie"),
        PageLink(page_id="link2", entity_type="Movie"),
    ]


def test_downloader_task_execute_with_TableOfContents(test_settings: Settings):
    """when the task is executed with a TableOfContents, it should extract the links and download each linked page."""

    client = StubSyncHttpClient(response="<html>Test Content</html>")

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
    result = execute_task(
        page=toc,
        settings=test_settings,
        http_client=client,
        storage_handler=storage_handler,
        link_extractor=extractor,
        return_results=True,
    )

    # then
    assert extractor._is_called is True
    assert result == ["link1", "link2"]
    assert storage_handler.is_inserted is True


def test_downloader_task_execute_with_PageLink(test_settings: Settings):
    """when the task is executed with a PageLink, it should download the page content."""

    client = StubSyncHttpClient(response="<html>Test Content</html>")

    storage_handler = StubStorage()

    page_link = PageLink(page_id="link1", entity_type="Movie")

    # when
    result = execute_task(
        page=page_link,
        settings=test_settings,
        http_client=client,
        storage_handler=storage_handler,
        return_results=True,
    )

    # then
    assert result == ["link1"]
    assert storage_handler.is_inserted is True


def test_downloader_task_execute_return_results(test_settings: Settings):
    """when the task is executed with a TableOfContents, it should extract the links and download each linked page."""

    client = StubSyncHttpClient(response="<html>Test Content</html>")
    storage_handler = StubStorage()

    page_link = PageLink(page_id="link1", entity_type="Movie")

    # when
    _ = execute_task(
        page=page_link,
        settings=test_settings,
        http_client=client,
        storage_handler=storage_handler,
        return_results=True,
    )

    # then
    assert storage_handler.is_inserted is True
