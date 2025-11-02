import uuid
from unittest.mock import patch

import pytest
import redis

from src.entities.person import Person
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.flows.extract import extract_entities_flow
from src.settings import AppSettings

from ..stubs.stub_analyzer import StubAnalyzer
from ..stubs.stub_section_search import StubSectionSearch


@pytest.fixture(scope="function", autouse=True)
def cleanup_storage(test_settings: AppSettings):
    """Helper to cleanup the Redis storages used in the tests"""
    r = redis.Redis.from_url(test_settings.storage_settings.redis_dsn)
    r.flushdb()
    yield
    r.flushdb()


def test_extract_entities_flow_of_a_page_non_existing(test_settings: AppSettings):
    """
    an on-demand extraction of a non-existing page should be triggered in this case
    """

    # given
    page_id = uuid.uuid4().hex  # random page_id

    # when
    with patch("src.repositories.orchestration.flows.extract.emit_event") as mock_emit:
        # Appelle la tâche Prefect (directement ou via .run si besoin)
        extract_entities_flow(
            app_settings=test_settings,
            entity_type="Person",
            page_id=page_id,
            refresh_cache=True,
        )

    # then
    # verify the event is emitted
    assert mock_emit.called
    mock_emit.assert_called_with(
        event="extract.entity",
        resource={"prefect.resource.id": page_id},
        payload={"entity_type": "Person"},
    )


def test_extract_entities_flow_for_given_page_id(
    test_settings: AppSettings, read_beethoven_html
):
    """extract entities from an existing page"""

    # given
    page_id = "some_page_id"

    # insert the HTML content into the HTML storage
    html_store = RedisTextStorage[Person](test_settings.storage_settings.redis_dsn)
    html_store.insert(content_id=page_id, content=read_beethoven_html)

    json_store = RedisJsonStorage[Person](test_settings.storage_settings.redis_dsn)

    entity_analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

    # the DB is empty
    assert list(json_store.scan()) == []

    # when
    extract_entities_flow(
        app_settings=test_settings,
        entity_type="Person",
        page_id=page_id,
        entity_analyzer=entity_analyzer,
        section_searcher=section_searcher,
        json_store=json_store,
        refresh_cache=True,  # force re-processing of all pages
    )

    # then
    # assert entity_analyzer.is_analyzed
    # assert section_searcher.is_called

    # there should be one entity stored in the JSON storage
    results = list(json_store.scan())
    assert len(results) == 1


def test_extract_entities_flow_for_all_pages(test_settings: AppSettings):

    # given
    # generate 3 pages in the HTML storage
    html_store = RedisTextStorage[Person](test_settings.storage_settings.redis_dsn)
    for i in range(3):
        html_store.insert(content_id=f"page_{i}", content=f"<html>content {i}</html>")

    json_store = RedisJsonStorage[Person](test_settings.storage_settings.redis_dsn)
    entity_analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

    # verify the DB is empty to start with
    assert list(json_store.scan()) == []

    # when
    extract_entities_flow(
        app_settings=test_settings,
        entity_type=Person.__name__,
        entity_analyzer=entity_analyzer,
        section_searcher=section_searcher,
        json_store=json_store,
        refresh_cache=True,  # force re-processing of all pages
    )

    # then
    assert entity_analyzer.is_analyzed
    assert section_searcher.is_called

    # wait a bit for the tasks to complete
    import time

    time.sleep(2)

    # there should be 3 entities stored in the JSON storage
    results = list(json_store.scan())
    assert len(results) == 3
