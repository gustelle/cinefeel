import tempfile
import uuid

import kuzu

from src.entities.film import Film
from src.repositories.db.graph_storage import GraphDBStorage
from src.settings import Settings


def test_graph_db_initialization():
    # given
    settings = Settings(
        db_persistence_directory=None,  # Use an in-memory database for testing
    )

    graph_db = GraphDBStorage[Film](settings)

    # when
    is_setup = graph_db.setup()

    # then
    assert is_setup is True


def test_insert_or_update():
    # given
    settings = Settings(
        db_persistence_directory=None,  # Use an in-memory database for testing
    )

    graph_db = GraphDBStorage[Film](settings)

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    # when
    graph_db.insert_many([film])

    # then
    retrieved_film = graph_db.select(film.uid)

    assert retrieved_film is not None
    assert retrieved_film.uid == film.uid


def test_insert_or_update_deduplication():
    # given
    settings = Settings(
        db_persistence_directory=None,  # Use an in-memory database for testing
    )

    graph_db = GraphDBStorage[Film](settings)

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    # when
    count = graph_db.insert_many([film, film])

    # This should not create a duplicate entry
    # then
    retrieved_film = graph_db.select(film.uid)

    assert retrieved_film is not None
    assert retrieved_film.uid == film.uid
    assert count == 1  # Only one film should be inserted


def test_get_nominal():
    # given
    settings = Settings(
        db_persistence_directory=None,  # Use an in-memory database for testing
    )

    graph_db = GraphDBStorage[Film](settings)

    film = Film(
        title="Inception",
        permalink="https://example.com/inception",
    )

    graph_db.insert_many([film])

    # when
    retrieved_film = graph_db.select(film.uid)

    # then
    assert retrieved_film is not None
    assert retrieved_film.uid == film.uid


def test_get_non_existent():
    # given
    settings = Settings(
        db_persistence_directory=None,  # Use an in-memory database for testing
    )

    graph_db = GraphDBStorage[Film](settings)

    non_existent_uid = uuid.uuid4().hex

    # when
    retrieved_film = graph_db.select(non_existent_uid)

    # then
    assert retrieved_film is None


def test_get_bad_data():
    # given

    # create a GraphDB instance with a bad data
    # and try to query a film
    with tempfile.TemporaryDirectory() as tmp_dir:

        settings = Settings(
            db_persistence_directory=tmp_dir,  # Use a temporary file for testing
        )

        file_name = f"{tmp_dir}/bad_data.json"

        # create a file with bad data
        with open(file_name, "w") as f:
            f.write('{"uid": "bad-uid", "poo": "Bad Film"}')

        # create a GraphDB instance
        client = kuzu.Database(settings.db_persistence_directory)

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

        graph_db = GraphDBStorage[Film](settings)

        # when
        result = graph_db.select("bad-uid")
        # then
        assert result is None
