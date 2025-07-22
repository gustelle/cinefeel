import pytest
from neo4j import GraphDatabase

from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.settings import Settings


@pytest.fixture(scope="module")
def test_db_settings():
    yield Settings(
        db_uri="bolt://localhost:7687",
    )


@pytest.fixture(scope="function")
def test_person_handler(test_db_settings):
    yield PersonGraphHandler(test_db_settings)


@pytest.fixture(scope="function")
def test_film_handler(test_db_settings):
    yield FilmGraphHandler(test_db_settings)


@pytest.fixture(scope="function")
def test_memgraph_client(test_db_settings):
    client = GraphDatabase.driver(
        str(test_db_settings.db_uri),
        auth=("", ""),
    )
    yield client
    client.close()
