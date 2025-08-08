import random

import redis
from pydantic import HttpUrl
from redis.commands.json.path import Path

from src.entities.film import Film
from src.repositories.db.redis.json import RedisJsonStorage
from src.settings import Settings


def test_redis_insert_dict(test_film: Film):
    """Test the insert method of RedisStorage with a dictionary."""

    # given
    settings = Settings()
    storage = RedisJsonStorage[Film](settings)

    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.json().delete(
        storage._get_key(test_film.uid)
    )  # Clear any existing content with the same ID

    # when
    storage.insert(test_film.uid, test_film)

    # then
    stored_content = r.json().get(storage._get_key(test_film.uid))

    assert isinstance(stored_content, dict), "Stored content should be a dictionary"
    assert stored_content["uid"] == test_film.uid, "UID should match the inserted film"
    assert (
        stored_content["title"] == test_film.title
    ), "Title should match the inserted film"

    r.json().delete(storage._get_key(test_film.uid))


def test_redis_select_film(test_film: Film):
    """Test the select method of RedisStorage with a dictionary."""

    # given
    settings = Settings()
    storage = RedisJsonStorage[Film](settings)

    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )

    r.json().delete(storage._get_key(test_film.uid))

    # Insert the content into Redis
    r.json().set(
        storage._get_key(test_film.uid),
        Path.root_path(),
        test_film.model_dump(mode="json"),
    )

    # Now select it
    retrieved_content = storage.select(test_film.uid)

    assert isinstance(
        retrieved_content, Film
    ), "Retrieved content should be a Film instance"
    assert retrieved_content.uid == test_film.uid, "UID should match the inserted film"

    r.json().delete(storage._get_key(test_film.uid))


def test_redis_scan_film(test_film: Film):
    """Test the scan method of RedisStorage with a dictionary."""

    # given
    settings = Settings()
    storage = RedisJsonStorage[Film](settings)

    test_film_1 = test_film.model_copy(deep=True)
    test_film_1.title = test_film_1.title + " 1"

    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.json().delete(storage._get_key(test_film_1.uid))
    r.json().delete(storage._get_key(test_film.uid))

    # Insert the content into Redis
    r.json().set(
        storage._get_key(test_film_1.uid),
        Path.root_path(),
        test_film_1.model_dump(mode="json"),
    )
    r.json().set(
        storage._get_key(test_film.uid),
        Path.root_path(),
        test_film.model_dump(mode="json"),
    )

    # Now scan it
    scanned_content = list(storage.scan())

    assert len(scanned_content) == 2, "Expected 2 items to be scanned"
    assert all(
        isinstance(item, Film) for item in scanned_content
    ), "All scanned items should be Film instances"

    r.json().delete(storage._get_key(test_film_1.uid))
    r.json().delete(storage._get_key(test_film.uid))


def test_redis_query(test_film: Film):
    """Test the query method of RedisStorage."""

    # given
    settings = Settings()
    storage = RedisJsonStorage[Film](settings)

    test_film_1 = test_film.model_copy(deep=True)
    test_film_1.title = test_film_1.title + " 1"
    test_film_1.permalink = HttpUrl(
        (str(test_film_1.permalink) + f"/{random.randint(1000, 9999)}")
    )

    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.json().delete(storage._get_key(test_film_1.uid))
    r.json().delete(storage._get_key(test_film.uid))

    # Insert the content into Redis
    r.json().set(
        storage._get_key(test_film_1.uid),
        Path.root_path(),
        test_film_1.model_dump(mode="json"),
    )
    r.json().set(
        storage._get_key(test_film.uid),
        Path.root_path(),
        test_film.model_dump(mode="json"),
    )

    # Now query it
    queried_content = storage.query(
        permalink=str(test_film_1.permalink),
    )

    assert len(queried_content) == 1
    assert isinstance(
        queried_content[0], Film
    ), "Queried content should be a Film instance"
    assert (
        queried_content[0].uid == test_film_1.uid
    ), "UID should match the queried film"
    assert (
        queried_content[0].title == test_film_1.title
    ), "Title should match the queried film"

    r.json().delete(storage._get_key(test_film_1.uid))
    r.json().delete(storage._get_key(test_film.uid))


def test_insert_many(test_film: Film):
    """Test the insert_many method of RedisStorage."""

    # given
    settings = Settings()
    storage = RedisJsonStorage[Film](settings)

    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.json().delete(storage._get_key(test_film.uid))

    # when
    storage.insert_many([test_film])

    # then
    stored_content = r.json().get(storage._get_key(test_film.uid))

    assert isinstance(stored_content, dict), "Stored content should be a dictionary"
    assert stored_content["uid"] == test_film.uid, "UID should match the inserted film"
    assert (
        stored_content["title"] == test_film.title
    ), "Title should match the inserted film"

    r.json().delete(storage._get_key(test_film.uid))
