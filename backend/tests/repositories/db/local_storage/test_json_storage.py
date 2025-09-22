import random
import uuid
from concurrent.futures import ThreadPoolExecutor

import orjson
import pytest
from pydantic import HttpUrl

from src.entities.movie import FilmSpecifications, Movie
from src.entities.person import Biography, Person, PersonMedia
from src.interfaces.storage import StorageError
from src.repositories.db.local_storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings


@pytest.fixture(scope="function", autouse=True)
def teardown(test_settings: Settings):

    # remove any contents of the directory
    # this may occur if the test is run multiple times
    local_path = test_settings.local_storage_directory
    movies_directory = local_path / "movies"
    movies_directory.mkdir(exist_ok=True)

    persons_directory = local_path / "persons"
    persons_directory.mkdir(exist_ok=True)

    # teardown
    # remove any contents of the directory
    # this may occur if the test is run multiple times
    for file in movies_directory.iterdir():
        file.unlink()

    for file in persons_directory.iterdir():
        file.unlink()

    yield

    # teardown
    # remove any contents of the directory
    # this may occur if the test is run multiple times
    for file in movies_directory.iterdir():
        file.unlink()
    try:
        movies_directory.rmdir()
    except OSError:
        pass

    for file in persons_directory.iterdir():
        file.unlink()
    try:
        persons_directory.rmdir()
    except OSError:
        pass


def test_dir_is_created(test_settings: Settings):
    """
    Test if the directory is created when the JSONEntityStorageHandler is initialized.
    """

    # when
    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    # then
    assert storage_handler.persistence_directory.exists()
    assert storage_handler.persistence_directory.is_dir()


def test_when_dir_already_exists(test_settings: Settings):

    # when
    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    # then
    # assert no exception is raised
    assert storage_handler.persistence_directory.exists()
    assert storage_handler.persistence_directory.is_dir()


def test_insert_film(test_settings: Settings):

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    content = {
        "title": "Test Film",
    }

    film = Movie(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
    )

    # when
    storage_handler.insert(film.uid, film)

    # then
    assert (storage_handler.persistence_directory / f"{film.uid}.json").exists()
    assert orjson.loads(
        (storage_handler.persistence_directory / f"{film.uid}.json").read_text()
    ) == film.model_dump(mode="json", exclude_none=True)


def test_insert_person(test_settings: Settings):

    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    # when
    content_id = "test_person"
    content = {
        "full_name": "Test Person",
    }

    person = Person(
        uid=content_id,
        title="Test Person Title",
        permalink=HttpUrl("http://example.com/test-person"),
    )

    person.biography = Biography(
        full_name=content["full_name"],
        parent_uid=person.uid,
    )

    storage_handler.insert(person.uid, person)

    # then
    assert (storage_handler.persistence_directory / f"{person.uid}.json").exists()
    assert orjson.loads(
        (storage_handler.persistence_directory / f"{person.uid}.json").read_text()
    ) == person.model_dump(mode="json", exclude_none=True)


def test_insert_bad_type(test_settings: Settings):

    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    # when
    content_id = "test_person"
    content = {
        "title": "Test Person",
    }

    film = Movie(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    # then
    with pytest.raises(StorageError) as e:
        storage_handler.insert(film.uid, film)

    assert "Error saving" in str(e.value)


def test_select_film(test_settings: Settings):

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    content_id = "test_film"
    content = {
        "title": "Test Film",
        "release_date": "2023-01-01",
        "directors": ["John Doe"],
        "duration": 120,
        "genres": ["Drama"],
    }

    film = Movie(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )
    film.specifications = FilmSpecifications(
        title=content["title"],
        parent_uid=film.uid,
        directed_by=content["directors"],
    )

    storage_handler.insert(film.uid, film)

    # when
    result = storage_handler.select(film.uid)

    # then
    assert result is not None
    assert result.uid == film.uid
    assert isinstance(result.specifications, FilmSpecifications)
    assert result.specifications.directed_by == content["directors"]


def test_select_non_existing_film(test_settings: Settings):

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    # when
    # delete all files in the directory to ensure the film does not exist
    for file in storage_handler.persistence_directory.iterdir():
        file.unlink()

    # generate a random uid
    uid = uuid.uuid4().hex

    # then
    assert storage_handler.select(uid) is None


def test_select_corrupt_entity(test_settings: Settings):

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    # when
    content_id = "test_film"
    content = {
        "title": "Test Film",
        "release_date": "2023-01-01",
        "directors": ["John Doe"],
        "duration": 120,
        "genres": ["Drama"],
    }

    film = Movie(
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


def test_query_person_nominal(test_settings: Settings):
    # given

    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    person = Person(
        title="Test Person Title",
        permalink=HttpUrl("http://example.com/test-person"),
    )
    person.biography = Biography(
        nom_complet="Test Person Biography", parent_uid=person.uid
    )
    person.media = PersonMedia(
        photos=["http://example.com/test-person-poster"],
        parent_uid=person.uid,
    )

    storage_handler.insert(person.uid, person)

    # when
    results = storage_handler.query()

    # then
    assert len(results) == 1
    assert results[0].uid == person.uid


def test_query_person_after(test_settings: Settings):

    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    person = Person(
        title="Test Person Title 1",
        permalink=HttpUrl("http://example.com/test-person-1"),
    )
    person.biography = Biography(
        nom_complet="Test Person Biography", parent_uid=person.uid
    )
    person.media = PersonMedia(
        photos=["http://example.com/test-person-poster"],
        parent_uid=person.uid,
    )
    other_person = Person(
        title="Test Person Title 2",
        permalink=HttpUrl("http://example.com/test-person-2"),
    )

    storage_handler.insert(person.uid, person)
    storage_handler.insert(other_person.uid, other_person)

    # when
    results = storage_handler.query(after=person)

    for result in results:
        print(result.model_dump_json(indent=2))

    # then
    assert not any(r.uid == person.uid for r in results)
    assert any(r.uid == other_person.uid for r in results)


def test_query_person_limit(test_settings: Settings):

    # given

    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    person = Person(
        title="Test Person Title",
        permalink=HttpUrl("http://example.com/test-person"),
    )
    person.biography = Biography(
        nom_complet="Test Person Biography", parent_uid=person.uid
    )
    person.media = PersonMedia(
        photos=["http://example.com/test-person-poster"],
        parent_uid=person.uid,
    )

    storage_handler.insert(person.uid, person)

    # when
    results = storage_handler.query(limit=1)

    # then
    assert len(results) == 1


def test_query_person_by_permalink(test_settings: Settings):
    # given

    storage_handler = JSONEntityStorageHandler[Person](test_settings)

    permalink = "http://example.com/test-person"

    person = Person(
        title="Test Person Title",
        permalink=HttpUrl(permalink),
    )

    storage_handler.insert(person.uid, person)

    # insert noise data
    noise_person = Person(
        title="Noise Person",
        permalink=HttpUrl("http://example.com/noise-person"),
    )
    storage_handler.insert(noise_person.uid, noise_person)

    # when
    results = storage_handler.query(permalink=permalink)

    # then
    assert len(results) == 1
    assert results[0].uid == person.uid


def test_query_no_files(test_settings: Settings):
    # given

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    # when
    results = storage_handler.query()

    # then
    assert len(results) == 0


def test_query_corrupt_file(test_settings: Settings):
    # given

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    content_id = "test_film"
    content = {
        "title": "Test Film",
    }

    film = Movie(
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


def test_query_validation_err(test_settings: Settings):
    # given

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    content_id = "test_film"
    content = {
        "title": "Test Film",
    }

    film = Movie(
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


def test_scan_film(test_settings: Settings):
    # given

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    content_id = "test_film"
    content = {
        "title": "Test Film",
    }

    film = Movie(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
        uid=content_id,
    )

    storage_handler.insert(film.uid, film)

    # when
    results = list(storage_handler.scan())

    # then
    assert len(results) == 1
    assert results[0].uid == film.uid


def test_scan_film_object_is_deeply_rebuilt(test_settings: Settings):
    # given

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    content = {
        "title": "Test Film",
    }

    film = Movie(
        title=content["title"],
        permalink=HttpUrl("http://example.com/test-film"),
    )
    film.specifications = FilmSpecifications(
        title=content["title"],
        parent_uid=film.uid,
        directed_by=["John Doe"],
    )

    storage_handler.insert(film.uid, film)

    # when
    results = list(storage_handler.scan())

    # then
    assert isinstance(results[0].specifications, FilmSpecifications)
    assert results[0].specifications.directed_by == ["John Doe"]


def test_query_thread_safety(test_settings: Settings):
    """
    verify that the query method is thread-safe and can be called concurrently.
    """

    # given

    storage_handler = JSONEntityStorageHandler[Movie](test_settings)

    uids = []
    n_threads = 4

    for i in range(1_000):
        permalink = HttpUrl(f"http://example.com/test-film/{i}")
        film = Movie(
            title=f"Test Film {i}",
            permalink=permalink,
        )
        storage_handler.insert(film.uid, film)
        uids.append(film.uid)

    # when
    # call concurrently

    with ThreadPoolExecutor(max_workers=n_threads) as executor:
        random_index = random.randint(0, len(uids) - 1)
        random_permalink = HttpUrl(f"http://example.com/test-film/{random_index}")
        for _ in range(n_threads):
            future = executor.submit(storage_handler.query, permalink=random_permalink)
            assert future.result() is not None
