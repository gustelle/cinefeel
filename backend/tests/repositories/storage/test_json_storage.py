from pathlib import Path

import orjson
import pytest
from pydantic import HttpUrl

from src.entities.film import Film
from src.entities.person import Biography, Person, PersonMedia
from src.interfaces.storage import StorageError
from src.repositories.storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings

current_dir = Path(__file__).parent


def test_dir_is_created():
    """
    Test if the directory is created when the JSONEntityStorageHandler is initialized.
    """

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)

    # when
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    # then
    assert storage_handler.persistence_directory.exists()
    assert storage_handler.persistence_directory.is_dir()

    # teardown
    # remove any contents of the directory
    # this may occur if the test is run multiple times
    for file in storage_handler.persistence_directory.iterdir():
        if file.is_file():
            file.unlink()
    storage_handler.persistence_directory.rmdir()


def test_when_dir_already_exists():

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    existing_dir = local_path / "films"
    existing_dir.mkdir()

    # when
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    # then
    # assert no exception is raised
    assert storage_handler.persistence_directory.exists()
    assert storage_handler.persistence_directory.is_dir()

    # teardown
    storage_handler.persistence_directory.rmdir()


def test_insert_film():

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    # when
    content_id = "test_film"
    content = {
        "title": "Test Film",
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    storage_handler.insert(film.uid, film)

    # then
    assert (storage_handler.persistence_directory / f"{film.uid}.json").exists()
    assert orjson.loads(
        (storage_handler.persistence_directory / f"{film.uid}.json").read_text()
    ) == film.model_dump(mode="json", exclude_none=True)

    # teardown
    (storage_handler.persistence_directory / f"{film.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()


def test_insert_person():

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    # when
    content_id = "test_person"
    content = {
        "full_name": "Test Person",
    }

    person = Person(
        uid=content_id,
        full_name=content["full_name"],
        title="Test Person Title",
        permalink=HttpUrl("http://example.com/test-person"),
    )

    storage_handler.insert(person.uid, person)

    # then
    assert (storage_handler.persistence_directory / f"{person.uid}.json").exists()
    assert orjson.loads(
        (storage_handler.persistence_directory / f"{person.uid}.json").read_text()
    ) == person.model_dump(mode="json", exclude_none=True)

    # teardown
    (storage_handler.persistence_directory / f"{person.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()


def test_insert_bad_type():

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    # when
    content_id = "test_person"
    content = {
        "title": "Test Person",
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    # then
    with pytest.raises(StorageError) as e:
        storage_handler.insert(film.uid, film)

    assert "Error saving" in str(e.value)

    # teardown
    storage_handler.persistence_directory.rmdir()


def test_select_film():

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    # when
    content_id = "test_film"
    content = {
        "title": "Test Film",
        "release_date": "2023-01-01",
        "directors": ["John Doe"],
        "duration": 120,
        "genres": ["Drama"],
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    storage_handler.insert(film.uid, film)

    # then
    assert storage_handler.select(film.uid) == film

    # teardown
    (storage_handler.persistence_directory / f"{film.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()


def test_select_non_existing_film():

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    # when
    content_id = "test_film"
    content = {
        "title": "Test Film",
        "release_date": "2023-01-01",
        "directors": ["John Doe"],
        "duration": 120,
        "genres": ["Drama"],
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    # then
    assert storage_handler.select(film.uid) is None

    # teardown
    storage_handler.persistence_directory.rmdir()


def test_select_corrupt_entity():

    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    # when
    content_id = "test_film"
    content = {
        "title": "Test Film",
        "release_date": "2023-01-01",
        "directors": ["John Doe"],
        "duration": 120,
        "genres": ["Drama"],
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    storage_handler.insert(film.uid, film)

    # corrupt the file
    (storage_handler.persistence_directory / f"{film.uid}.json").write_text(
        "corrupt data"
    )

    # then
    assert storage_handler.select(film.uid) is None

    # teardown
    (storage_handler.persistence_directory / f"{film.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()


def test_query_film():
    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    content_id = "test_film"
    content = {
        "title": "Test Film",
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    storage_handler.insert(film.uid, film)

    # when
    results = storage_handler.query()

    # then
    assert len(results) == 1
    assert results[0].uid == film.uid

    # teardown
    (storage_handler.persistence_directory / f"{film.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()


def test_query_person():
    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    content_id = "test_person"
    content = {
        "full_name": "Test Person",
    }

    person = Person(
        uid=content_id,
        full_name=content["full_name"],
        title="Test Person Title",
        permalink=HttpUrl("http://example.com/test-person"),
        biography=Biography(uid="1", nom_complet="Test Person Biography"),
        media=PersonMedia(
            uid="1",
            url_affiche="http://example.com/test-person-poster",
        ),
    )

    storage_handler.insert(person.uid, person)

    # when
    results = storage_handler.query()

    # then
    assert len(results) == 1
    assert results[0].uid == person.uid

    # teardown
    (storage_handler.persistence_directory / f"{person.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()


def test_query_no_files():
    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    # when
    results = storage_handler.query()

    # then
    assert len(results) == 0

    # teardown
    storage_handler.persistence_directory.rmdir()


def test_query_corrupt_file():
    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    content_id = "test_film"
    content = {
        "title": "Test Film",
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    storage_handler.insert(film.uid, film)

    # corrupt the file
    (storage_handler.persistence_directory / f"{film.uid}.json").write_text(
        "corrupt data"
    )

    # when
    with pytest.raises(StorageError) as e:
        storage_handler.query()

    # then
    assert "Error validating data" in str(e.value)

    # teardown
    (storage_handler.persistence_directory / f"{film.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()


def test_query_validation_err():
    # given
    local_path = current_dir
    test_settings = Settings(persistence_directory=local_path)
    storage_handler = JSONEntityStorageHandler[Film](test_settings)

    content_id = "test_film"
    content = {
        "title": "Test Film",
    }

    film = Film(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    storage_handler.insert(film.uid, film)

    # corrupt the file
    (storage_handler.persistence_directory / f"{film.uid}.json").write_text(
        orjson.dumps({"hey": "there"}).decode()
    )

    # when
    with pytest.raises(StorageError) as e:
        storage_handler.query()

    # then
    assert "Error validating data" in str(e.value)

    # teardown
    (storage_handler.persistence_directory / f"{film.uid}.json").unlink()
    storage_handler.persistence_directory.rmdir()
