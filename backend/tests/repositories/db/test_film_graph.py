import tempfile
import uuid
from pathlib import Path

import kuzu
import pytest
from neo4j import GraphDatabase
from neo4j.graph import Node
from pydantic import ValidationError

from src.entities.film import Film, FilmSpecifications
from src.entities.person import Person
from src.interfaces.relation_manager import PeopleRelationshipType, Relationship
from src.interfaces.storage import StorageError
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.settings import Settings


def test_insert_a_film(
    test_memgraph_client: GraphDatabase,
    test_film_handler: FilmGraphHandler,
    test_film: Film,
):
    """assert the data type is correct when inserting a film"""

    # given
    # drop all existing data

    test_memgraph_client.execute_query("MATCH (n:Film) DETACH DELETE n")

    # when
    count = test_film_handler.insert_many([test_film])

    # then
    assert count == 1  # Only one film should be inserted

    # select the film to verify its type
    records, _, _ = test_memgraph_client.execute_query(
        f"""
        MATCH (n:Film {{uid: '{test_film.uid}'}})
        RETURN n LIMIT 1;
        """
    )
    film_data: Node = records[0].get("n", {})

    assert film_data is not None
    assert "uid" in film_data
    assert "title" in film_data
    assert "permalink" in film_data
    assert "media" in film_data
    assert "influences" in film_data
    assert "specifications" in film_data
    assert "actors" in film_data

    for field, value in film_data.items():
        if field == "uid":
            assert isinstance(value, str)
        elif field == "title":
            assert isinstance(value, str)
        elif field == "permalink":
            assert isinstance(value, str)
        elif field in ["media"]:
            assert (
                isinstance(value, dict)
                and "posters" in value
                and isinstance(value["posters"], list)
            )
        elif field in ["influences"]:
            assert isinstance(value, list) and all(
                isinstance(item, dict) for item in value
            )
        elif field in ["specifications"]:
            assert (
                isinstance(value, dict)
                and "written_by" in value
                and isinstance(value["written_by"], list)
            )
        elif field in ["actors"]:
            assert isinstance(value, list) and all(
                isinstance(actor, dict) for actor in value
            )

    # tear down the database
    with test_film_handler.client as driver:
        driver.execute_query("MATCH (n:Film) DETACH DELETE n")


def test_insert_several_films(
    test_memgraph_client: GraphDatabase,
    test_film_handler: FilmGraphHandler,
    test_film: Film,
):
    """assert several films can be inserted at once"""

    # given
    test_memgraph_client.execute_query("MATCH (n:Film) DETACH DELETE n")
    other_film = test_film.model_copy(deep=True)
    other_film.title = "The Dark Knight"

    # when
    count = test_film_handler.insert_many([test_film, other_film])

    # then
    assert count == 2  # Two films should be inserted

    # tear down the database
    with test_film_handler.client as driver:
        driver.execute_query("MATCH (n:Film) DETACH DELETE n")


def test_update_a_film(
    test_memgraph_client: GraphDatabase,
    test_film_handler: FilmGraphHandler,
    test_film: Film,
):
    """assert a film can be updated if it already exists in the database

    TODO: update deep fields like media, influences, specifications, actors
    """

    # given
    test_memgraph_client.execute_query("MATCH (n:Film) DETACH DELETE n")
    test_film_handler.insert_many([test_film])

    # when
    updated_film = test_film.model_copy(deep=True)
    updated_film.title = "Inception (Updated)"
    c = test_film_handler.insert_many([updated_film])

    # then
    assert c == 1  # Only one film should be updated
    # check if the film was updated
    records, _, _ = test_memgraph_client.execute_query(
        f"""
        MATCH (n:Film {{uid: '{updated_film.uid}'}})
        RETURN n LIMIT 1;
        """
    )
    film_data: Node = records[0].get("n", {})
    assert film_data is not None
    assert film_data.get("title") == "Inception (Updated)"

    # tear down the database
    with test_film_handler.client as driver:
        driver.execute_query("MATCH (n:Film) DETACH DELETE n")


def test_insert_existing(test_film_handler: FilmGraphHandler):
    """assert a film identified by its uid can be inserted or updated,
    there is no duplicate
    """

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


def test_insert_new(test_film_handler: FilmGraphHandler):
    """assert a film identified by its uid can be inserted or updated,
    there is no duplicate
    """

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


def test_insert_or_update_deduplication(test_film_handler: FilmGraphHandler):
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


def test_get_nominal(test_film_handler: FilmGraphHandler):
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


def test_get_non_existent(test_film_handler: FilmGraphHandler):
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
        client = kuzu.Database(Path(tmp_dir) / "test.db")

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

        graph_db = FilmGraphHandler(
            client=client,
            settings=Settings(
                db_path=Path(tmp_dir) / "test.db",  # Use the temporary directory
                db_max_size=1 * 1024 * 1024 * 1024,  # 1 GB for testing
            ),
        )

        # when
        result = graph_db.select("bad-uid")
        # then
        assert result is None


def test_add_relationship_person(test_film_handler: FilmGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FilmGraphHandler(
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
    assert isinstance(result, Relationship)


def test_add_relationship_non_existent_film(test_film_handler: FilmGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FilmGraphHandler(
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


def test_add_relationship_non_existent_person(test_film_handler: FilmGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FilmGraphHandler(
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


def test_add_invalid_relationship(test_film_handler: FilmGraphHandler):
    # given

    client = kuzu.Database(test_film_handler.client.database_path)

    film_db = FilmGraphHandler(
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


def test_select_film(test_film_handler: FilmGraphHandler):
    # given

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )
    specifications = FilmSpecifications(
        parent_uid=film.uid,
        title="Inception",
        duration=148,
        release_date="2010-07-16",
        genres=["Science Fiction", "Action"],
        written_by=["Christopher Nolan"],
    )
    film.specifications = specifications

    test_film_handler.insert_many([film])

    # when
    retrieved_film = test_film_handler.select(film.uid)

    # then
    assert retrieved_film is not None
    assert retrieved_film.specifications.duration == specifications.duration
    assert retrieved_film.specifications.release_date == specifications.release_date
    assert retrieved_film.specifications.genres == specifications.genres
    assert retrieved_film.specifications.written_by == specifications.written_by


def test_get_related_person_single():
    """caveat: make sure the db is shared between the two handlers
    if using defaut memory db, this will not work
    """
    # given

    cur_dir = Path(__file__).parent

    settings = Settings(
        db_path=Path(cur_dir) / "test.db",  # Use the temporary directory
        db_max_size=1 * 1024 * 1024 * 1024,  # 1 GB for testing
    )

    person_db = PersonGraphHandler(
        None,
        settings=settings,
    )

    film_db = FilmGraphHandler(
        None,
        settings=settings,
    )

    film1 = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )
    specifications = FilmSpecifications(
        parent_uid=film1.uid,
        title="Inception",
        duration="02:28:00",
        release_date="2010-07-16",
        genres=["Science Fiction", "Action"],
        written_by=["Christopher Nolan"],
    )
    film1.specifications = specifications
    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )

    film_db.insert_many([film1])
    person_db.insert_many([person])

    film_db.add_relationship(film1, PeopleRelationshipType.DIRECTED_BY, person)

    # when
    relations = film_db.get_related(film1, PeopleRelationshipType.DIRECTED_BY)

    # then
    assert isinstance(relations, list)
    assert len(relations) == 1  # One relationship added
    assert relations[0].to_entity.title == person.title
    assert relations[0].from_entity.title == film1.title
    assert relations[0].relation_type == PeopleRelationshipType.DIRECTED_BY

    # Cleanup
    Path(cur_dir / "test.db").unlink(missing_ok=True)  # Remove the test database file
