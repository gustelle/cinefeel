import shutil
from pathlib import Path
from unittest.mock import Mock

import orjson
from neo4j import GraphDatabase

from src.entities.person import Person
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.task_orchestration.extraction_pipeline import (
    UnitExtractionPipeline,
)
from src.settings import Settings

from .stubs.stub_http import StubSyncHttpClient


def test_unit_extraction_pipeline(
    prefect_harness,
    test_person_graphdb: PersonGraphHandler,
    test_memgraph_client: GraphDatabase,
    read_melies_html: str,
    mocker: Mock,
):
    """we'll mock lots of things here, so we can focus on the extraction pipeline logic"""

    # given
    test_memgraph_client.execute_query("MATCH (n:Film), (m:Person) DETACH DELETE n, m")

    test_path = Path(__file__).parent / "test_data"
    test_path.mkdir(exist_ok=True)

    shutil.rmtree(test_path, ignore_errors=True)

    permalink = "https://en.wikipedia.org/wiki/Test_Person"

    http_client = StubSyncHttpClient(
        response=read_melies_html,
    )
    settings = Settings(
        persistence_directory=test_path,
        meili_base_url=None,  # do not index for this test, it's not relevant
        graph_db_uri="bolt://localhost:7687",
    )

    mocker.patch(
        "src.repositories.task_orchestration.extraction_pipeline.HtmlParsingFlow.execute",
    )

    parsed_json = {
        "permalink": permalink,
        "uid": "test_person",
        "title": "test-person",
    }

    # assume the content is correctly parsed, check it's stored in the DB
    # make sure the parent folder exists
    (test_path / "persons").mkdir(parents=True, exist_ok=True)
    file_path = Path(
        test_path / "persons/test-person.json",
    )

    with open(file_path, "w") as f:
        f.write(orjson.dumps(parsed_json).decode("utf-8"))

    pipeline = UnitExtractionPipeline(
        settings=settings,
        entity_type=Person,
        http_client=http_client,
    )
    pipeline.execute_pipeline(
        permalink=permalink,
    )

    # then
    # pick the content from the DB storage
    results = test_person_graphdb.query(permalink=permalink)
    assert len(results) == 1
    assert str(results[0].permalink) == permalink

    # cleanup
    shutil.rmtree(test_path, ignore_errors=True)
    test_memgraph_client.execute_query("MATCH (n:Film), (m:Person) DETACH DELETE n, m")
