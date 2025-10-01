import os
import uuid

import pytest

from src.entities.person import Person
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.flows.entities_extraction import (
    extract_entities_flow,
)
from src.settings import Settings

from ..stubs.stub_analyzer import StubAnalyzer
from ..stubs.stub_section_search import StubSectionSearch


def test_extract_entities_flow_of_a_page_non_existing(test_settings: Settings):
    # given
    page_id = uuid.uuid4().hex  # random page_id

    # when
    with pytest.raises(ValueError) as v:
        extract_entities_flow.fn(
            settings=test_settings, entity_type="Movie", page_id=page_id
        )

    # then
    assert "page_id" in str(v.value)


def test_extract_entities_flow_nominal(test_settings: Settings, read_beethoven_html):
    """extract entities from an existing page

    TODO:
    --> need to have control over the entity_id generation from the beginning
    --> so that we keep the same id between the HTML and the JSON storage
    --> we could take as id the entity name + page_id slugified, ex: "Person:Ludwig_van_Beethoven"
    """

    # given
    os.environ["TOKENIZERS_PARALLELISM"] = "false"  # use a different Redis DB for tests
    page_id = "some_page_id"

    # insert the HTML content into the HTML storage
    html_store = RedisTextStorage(settings=test_settings)
    html_store.insert(content_id=page_id, content=read_beethoven_html)

    json_store = RedisJsonStorage[Person](settings=test_settings)
    entity_analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

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
    # select the extracted entities from the JSON storage
    extracted_entities = json_store.select(content_id=page_id)

    # assert the extracted entities
    assert len(extracted_entities) == 1
    print(extracted_entities[0])
