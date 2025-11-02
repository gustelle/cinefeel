import random

import orjson
import pytest
import redis
from pydantic import HttpUrl
from redis.commands.json.path import Path

from src.entities.movie import Movie
from src.repositories.db.redis.json import RedisJsonStorage
from src.settings import AppSettings


@pytest.fixture(scope="function", autouse=True)
def cleanup_redis(test_settings: AppSettings):
    """Cleans up the Redis database used for testing."""
    r = redis.Redis.from_url(
        str(test_settings.storage_settings.redis_dsn), decode_responses=True
    )
    r.flushdb()
    yield
    r.flushdb()


def test_redis_json_insert_dict(test_film: Movie, test_settings: AppSettings):
    """Test the insert method of RedisStorage with a dictionary."""

    # given

    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    r = redis.Redis.from_url(
        str(test_settings.storage_settings.redis_dsn), decode_responses=True
    )

    # when
    storage.insert(test_film.uid, test_film)

    # then
    stored_content = r.json().get(test_film.uid, Path.root_path())

    assert isinstance(stored_content, dict), "Stored content should be a dictionary"
    assert stored_content["uid"] == test_film.uid, "UID should match the inserted film"
    assert (
        stored_content["title"] == test_film.title
    ), "Title should match the inserted film"


def test_redis_json_select_film(test_film: Movie, test_settings: AppSettings):
    """Test the select method of RedisStorage with a dictionary."""

    # given

    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    r = redis.Redis.from_url(
        str(test_settings.storage_settings.redis_dsn), decode_responses=True
    )

    # Insert the content into Redis
    r.json().set(
        test_film.uid,
        Path.root_path(),
        test_film.model_dump(mode="json"),
    )

    # Now select it
    retrieved_content = storage.select(test_film.uid)

    assert isinstance(
        retrieved_content, Movie
    ), "Retrieved content should be a Film instance"
    assert retrieved_content.uid == test_film.uid, "UID should match the inserted film"


def test_redis_json_scan_film(test_film: Movie, test_settings: AppSettings):
    """Test the scan method of RedisStorage with a dictionary."""

    # given

    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    test_film_1 = test_film.model_copy(deep=True)
    test_film_1.title = test_film_1.title + " 1"

    r = redis.Redis.from_url(
        str(test_settings.storage_settings.redis_dsn), decode_responses=True
    )

    # Insert the content into Redis
    r.json().set(
        test_film_1.uid,
        Path.root_path(),
        test_film_1.model_dump(mode="json"),
    )
    r.json().set(
        test_film.uid,
        Path.root_path(),
        test_film.model_dump(mode="json"),
    )

    # Now scan it
    scanned_content = list(storage.scan())

    for item in scanned_content:
        print(f"Scanned id: {item[0]}, Title: {item[1].uid}")

    assert len(scanned_content) == 2, "Expected 2 items to be scanned"
    assert any(
        item[0] == test_film_1.uid and item[1].uid == test_film_1.uid
        for item in scanned_content
    ), "Scanned content should include the first film"
    assert any(
        item[0] == test_film.uid and item[1].uid == test_film.uid
        for item in scanned_content
    ), "Scanned content should include the second film"
    assert all(
        isinstance(item[1], Movie) for item in scanned_content
    ), "All scanned items should be Film instances"


def test_redis_json_query_by_permalink(test_film: Movie, test_settings: AppSettings):
    """Test the query method of RedisStorage."""

    # given

    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    test_film_1 = test_film.model_copy(deep=True)
    test_film_1.title = test_film_1.title + " 1"
    test_film_1.permalink = HttpUrl(
        (str(test_film_1.permalink) + f"/{random.randint(1000, 9999)}")
    )

    r = redis.Redis.from_url(
        str(test_settings.storage_settings.redis_dsn), decode_responses=True
    )

    # Insert the content into Redis
    r.json().set(
        test_film_1.uid,
        Path.root_path(),
        test_film_1.model_dump(mode="json"),
    )
    r.json().set(
        test_film.uid,
        Path.root_path(),
        test_film.model_dump(mode="json"),
    )

    # Now query it
    queried_content = storage.query(
        permalink=str(test_film_1.permalink),
    )

    assert len(queried_content) == 1
    assert isinstance(
        queried_content[0], Movie
    ), "Queried content should be a Film instance"
    assert (
        queried_content[0].uid == test_film_1.uid
    ), "UID should match the queried film"


def test_redis_json_hashing_is_deterministic(
    test_film: Movie, test_settings: AppSettings
):
    """Test that the uid_hash is deterministic for the same UID."""

    # given
    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    # when
    hash1 = storage._get_uid_hash(test_film)
    hash2 = storage._get_uid_hash(test_film)

    # then
    assert hash1 == hash2, "UID hash should be deterministic and consistent"


def test_redis_json_query_after(test_film: Movie, test_settings: AppSettings):
    """Test the query method of RedisStorage with 'after' parameter."""

    # given
    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    test_film_1 = test_film.model_copy(deep=True)
    test_film_1.title = test_film_1.title + " 1"
    test_film_1.permalink = HttpUrl(
        (str(test_film_1.permalink) + f"/{random.randint(1000, 9999)}")
    )

    test_film_2 = test_film.model_copy(deep=True)
    test_film_2.title = test_film_2.title + " 2"
    test_film_2.permalink = HttpUrl(
        (str(test_film_2.permalink) + f"/{random.randint(1000, 9999)}")
    )

    test_film_3 = test_film.model_copy(deep=True)
    test_film_3.title = test_film_3.title + " 3"
    test_film_3.permalink = HttpUrl(
        (str(test_film_3.permalink) + f"/{random.randint(1000, 9999)}")
    )

    test_film_4 = test_film.model_copy(deep=True)
    test_film_4.title = test_film_4.title + " 4"
    test_film_4.permalink = HttpUrl(
        (str(test_film_4.permalink) + f"/{random.randint(1000, 9999)}")
    )

    # when
    storage.insert_many([test_film, test_film_1, test_film_2, test_film_3, test_film_4])

    # then
    queried_content = storage.query(after=test_film_1)

    assert not any(
        item.uid == test_film_1.uid for item in queried_content
    ), "Queried content should not include the 'after' film"

    # now go on querying after the last one
    queried_content = storage.query(after=queried_content[-1])

    assert (
        not queried_content
    ), "No more content should be available after the last film"


def test_redis_json_insert_many(test_film: Movie, test_settings: AppSettings):
    """Test the insert_many method of RedisStorage."""

    # given
    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    r = redis.Redis.from_url(
        str(test_settings.storage_settings.redis_dsn), decode_responses=True
    )

    # when
    storage.insert_many([test_film])

    # then
    stored_content = r.json().get(test_film.uid, Path.root_path())

    assert isinstance(stored_content, dict), "Stored content should be a dictionary"
    assert stored_content["uid"] == test_film.uid, "UID should match the inserted film"
    assert (
        stored_content["title"] == test_film.title
    ), "Title should match the inserted film"


def test_redis_json_is_json_serializable(test_settings: AppSettings):
    """serialization is required for Prefect storage serializers"""

    # given
    storage = RedisJsonStorage[Movie](str(test_settings.storage_settings.redis_dsn))
    storage.on_init()

    # when
    serialized = orjson.dumps(storage, default=lambda o: o.__dict__)

    # then
    assert isinstance(serialized, bytes), "Serialized storage should be bytes"
