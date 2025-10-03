import uuid

import pytest
import redis

from src.entities.person import Person
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.flows.entities_extraction import (
    extract_entities_flow,
)
from src.settings import Settings

from ..stubs.stub_analyzer import StubAnalyzer
from ..stubs.stub_section_search import StubSectionSearch


@pytest.fixture(scope="function", autouse=True)
def cleanup_storage(test_settings: Settings):
    """Helper to cleanup the Redis storages used in the tests"""
    r = redis.Redis(
        host=test_settings.redis_storage_dsn.host,
        port=test_settings.redis_storage_dsn.port,
        db=(
            test_settings.redis_storage_dsn.path.lstrip("/")
            if test_settings.redis_storage_dsn.path
            else 0
        ),
        username=test_settings.redis_storage_dsn.username,
        password=test_settings.redis_storage_dsn.password,
        decode_responses=True,
    )
    r.flushdb()
    yield
    r.flushdb()


def test_extract_entities_flow_of_a_page_non_existing(test_settings: Settings):
    # given
    page_id = uuid.uuid4().hex  # random page_id

    # when
    with pytest.raises(ValueError) as v:
        extract_entities_flow(
            settings=test_settings, entity_type="Movie", page_id=page_id
        )

    # then
    assert "page_id" in str(v.value)


def test_extract_entities_flow_for_given_page_id(
    test_settings: Settings, read_beethoven_html
):
    """extract entities from an existing page"""

    # given
    page_id = "some_page_id"

    # insert the HTML content into the HTML storage
    html_store = RedisTextStorage(settings=test_settings)
    html_store.insert(content_id=page_id, content=read_beethoven_html)

    json_store = RedisJsonStorage[Person](settings=test_settings)

    entity_analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

    # the DB is empty
    assert list(json_store.scan()) == []

    # when
    extract_entities_flow(
        settings=test_settings,
        entity_type="Person",
        page_id=page_id,
        entity_analyzer=entity_analyzer,
        section_searcher=section_searcher,
        json_store=json_store,
    )

    # then
    assert entity_analyzer.is_analyzed
    assert section_searcher.is_called

    # there should be one entity stored in the JSON storage
    results = list(json_store.scan())
    assert len(results) == 1


def test_extract_entities_flow_for_all_pages(test_settings: Settings):

    # given
    # generate data in the HTML storage
    html_store = RedisTextStorage(settings=test_settings)
    for i in range(3):
        html_store.insert(content_id=f"page_{i}", content=f"<html>content {i}</html>")

    json_store = RedisJsonStorage[Person](settings=test_settings)
    entity_analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

    # the DB is empty
    assert list(json_store.scan()) == []

    # when
    extract_entities_flow(
        settings=test_settings,
        entity_type="Person",
        entity_analyzer=entity_analyzer,
        section_searcher=section_searcher,
        json_store=json_store,
    )

    # then
    assert entity_analyzer.is_analyzed
    assert section_searcher.is_called

    # there should be one entity stored in the JSON storage
    results = list(json_store.scan())
    assert len(results) == 3
