import tempfile
import uuid

import kuzu
import pytest
from pydantic import ValidationError

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.relation_manager import PeopleRelationshipType, Relationship
from src.interfaces.storage import StorageError
from src.repositories.db.film_graph import FimGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.settings import Settings


@pytest.fixture(scope="module")
def test_db_settings():

    yield Settings(
        db_persistence_directory=None,  # Use in-memory database for testing
        db_max_size=1 * 1024 * 1024 * 1024,  # 1 GB for testing
    )


@pytest.fixture(scope="function")
def test_film_handler(test_db_settings):
    yield FimGraphHandler(None, test_db_settings)


def test_graph_db_initialization(test_film_handler: FimGraphHandler):
    # given

    # when
    is_setup = test_film_handler.setup()

    # then
    assert is_setup is True


def test_insert_or_update(test_film_handler: FimGraphHandler):
    # given

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    # when
    test_film_handler.insert_many([film])

    # then
    retrieved_film = test_film_handler.select(film.uid)

    assert retrieved_film is not None
    assert retrieved_film.uid == film.uid


def test_insert_or_update_deduplication(test_film_handler: FimGraphHandler):
    # given

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    # when
    count = test_film_handler.insert_many([film, film])

    # This should not create a duplicate entry
    # then
    retrieved_film = test_film_handler.select(film.uid)

    assert retrieved_film is not None
    assert retrieved_film.uid == film.uid
    assert count == 1  # Only one film should be inserted


def test_get_nominal(test_film_handler: FimGraphHandler):
    # given

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    test_film_handler.insert_many([film])

    # when
    retrieved_film = test_film_handler.select(film.uid)

    # then
    assert retrieved_film is not None
    assert retrieved_film.uid == film.uid


def test_get_non_existent(test_film_handler: FimGraphHandler):
    # given

    non_existent_uid = uuid.uuid4().hex

    # when
    retrieved_film = test_film_handler.select(non_existent_uid)

    # then
    assert retrieved_film is None


def test_get_bad_data():
    # given

    # create a GraphDB instance with a bad data
    # and try to query a film
    with tempfile.TemporaryDirectory() as tmp_dir:

        file_name = f"{tmp_dir}/bad_data.json"

        # create a file with bad data
        with open(file_name, "w") as f:
            f.write('{"uid": "bad-uid", "poo": "Bad Film"}')

        # create a GraphDB instance
        client = kuzu.Database(tmp_dir)

        conn = kuzu.Connection(client)

        conn.execute("INSTALL json;LOAD json;")

        # insert bad data
        conn.execute(
            """
                CREATE NODE TABLE Film (
                    uid STRING,
                    poo STRING,
                    PRIMARY KEY (uid)
                );
            """
        )
        conn.execute(
            f"""
            COPY Film FROM '{file_name}' (file_format = 'json');
            """
        )

        graph_db = FimGraphHandler(
            client=client,
            settings=Settings(
                db_persistence_directory=tmp_dir,  # Use the temporary directory
                db_max_size=1 * 1024 * 1024 * 1024,  # 1 GB for testing
            ),
        )

        # when
        result = graph_db.select("bad-uid")
        # then
        assert result is None


def test_add_relationship_person(test_film_handler: FimGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FimGraphHandler(
        client=client,
    )

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    person_db = PersonGraphHandler(client=client)

    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )

    film_db.insert_many([film])
    person_db.insert_many([person])

    # when
    result = film_db.add_relationship(film, PeopleRelationshipType.DIRECTED_BY, person)

    # then
    assert film_db.person_client.select(person.uid) is not None
    assert isinstance(result, Relationship)


def test_add_relationship_non_existent_film(test_film_handler: FimGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FimGraphHandler(
        client=client,
    )

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    person_db = PersonGraphHandler(client=client)

    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )

    person_db.insert_many([person])

    # when
    with pytest.raises(StorageError) as exc_info:
        film_db.add_relationship(film, PeopleRelationshipType.DIRECTED_BY, person)

    # then
    assert "Content with ID" in str(exc_info.value)
    assert "does not exist in the database" in str(exc_info.value)


def test_add_relationship_non_existent_person(test_film_handler: FimGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FimGraphHandler(
        client=client,
    )

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    film_db.insert_many([film])

    non_existent_person = Person(
        title="Non Existent Person",
        permalink="https://example.com/non-existent-person",
    )

    # when
    with pytest.raises(StorageError) as exc_info:
        film_db.add_relationship(
            film, PeopleRelationshipType.DIRECTED_BY, non_existent_person
        )

    # then
    assert "Related content with ID" in str(exc_info.value)
    assert "does not exist in the database" in str(exc_info.value)


def test_add_invalid_relationship(test_film_handler: FimGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FimGraphHandler(
        client=client,
    )

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    person_db = PersonGraphHandler(client=client)

    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )

    film_db.insert_many([film])
    person_db.insert_many([person])

    # when
    with pytest.raises(ValidationError) as exc_info:
        film_db.add_relationship(film, "INVALID_RELATIONSHIP_TYPE", person)

    # then
    assert "INVALID_RELATIONSHIP_TYPE" in str(exc_info.value)
