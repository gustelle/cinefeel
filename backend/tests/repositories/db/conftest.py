import pytest
from neo4j import GraphDatabase

from src.entities.film import Film, FilmActor, FilmMedia, FilmSpecifications
from src.entities.person import Biography, GenderEnum, Person, PersonCharacteristics
from src.entities.woa import WOAInfluence, WOAType
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


@pytest.fixture(scope="function")
def test_film():
    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )
    film.influences = [
        WOAInfluence(
            parent_uid=film.uid,
            type=WOAType.FILM,
            persons=["Christopher Nolan"],
        ),
    ]
    film.media = FilmMedia(
        **{
            "parent_uid": film.uid,
            "posters": [
                "https://example.com/poster1.jpg",
                "https://example.com/poster2.jpg",
            ],
        }
    )
    film.specifications = FilmSpecifications(
        parent_uid=film.uid,
        title="Inception",
        written_by=["Christopher Nolan"],
    )

    film.actors = [
        FilmActor(
            parent_uid=film.uid,
            full_name="Leonardo DiCaprio",
        ),
        FilmActor(
            parent_uid=film.uid,
            full_name="Joseph Gordon-Levitt",
        ),
    ]
    yield film


@pytest.fixture(scope="function")
def test_person():
    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )

    person.biography = Biography(
        parent_uid=person.uid,
        full_name="Christopher Nolan",
    )

    person.characteristics = PersonCharacteristics(
        parent_uid=person.uid,
        gender=GenderEnum.MALE,
    )

    yield person
