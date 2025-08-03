import pytest
import redis
from redis.commands.json.path import Path

from src.repositories.db.redis import RedisStorage
from src.settings import Settings


def test_redis_bad_type():
    """Test that RedisStorage raises TypeError for unsupported types."""

    settings = Settings()

    with pytest.raises(TypeError):
        RedisStorage[int](settings)


def test_redis_insert():
    """Test the insert method of RedisTextStorage."""

    settings = Settings()
    storage = RedisStorage[str](settings)

    content_id = "test_content"
    content = "<html><body>Test Content</body></html>"

    # make sure the content does not already exist
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.delete(f"str:{content_id}")  # Clear any existing content with the same ID

    # when
    storage.insert(content_id, content)

    # then
    stored_content = r.get(f"str:{content_id}")

    assert (
        stored_content == content
    ), f"Expected '{content}', but got '{stored_content}'"
    r.delete(f"str:{content_id}")


def test_redis_insert_dict():
    """Test the insert method of RedisStorage with a dictionary."""

    settings = Settings()
    storage = RedisStorage[dict](settings)

    content_id = "test_content_dict"
    content = {"key": "value", "another_key": "another_value"}

    # make sure the content does not already exist
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.json().delete(f"dict:{content_id}")  # Clear any existing content with the same ID

    # when
    storage.insert(content_id, content)

    # then
    stored_content = r.json().get(f"dict:{content_id}")

    assert content == stored_content, f"Expected {content}, but got {stored_content}"

    r.json().delete(f"dict:{content_id}")


def test_redis_select():
    """Test the select method of RedisTextStorage."""

    # given
    settings = Settings()
    storage = RedisStorage[str](settings)

    content_id = "test_content"
    content = "<html><body>Test Content</body></html>"
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )

    r.delete("str:" + content_id)

    # Insert the content into Redis
    r.set(f"str:{content_id}", content)

    # Now select it
    retrieved_content = storage.select(content_id)

    assert (
        retrieved_content == content
    ), f"Expected '{content}', but got '{retrieved_content}'"
    r.delete("str:" + content_id)


def test_redis_select_dict():
    """Test the select method of RedisStorage with a dictionary."""

    # given
    settings = Settings()
    storage = RedisStorage[dict](settings)

    content_id = "test_content_dict"
    content = {"key": "value", "another_key": "another_value"}
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )

    r.json().delete("dict:" + content_id)

    # Insert the content into Redis
    r.json().set(f"dict:{content_id}", Path.root_path(), content)

    # Now select it
    retrieved_content = storage.select(content_id)

    assert (
        content == retrieved_content
    ), f"Expected {content}, but got {retrieved_content}"

    r.json().delete("dict:" + content_id)


def test_redis_scan():
    """Test the scan method of RedisTextStorage."""

    # given
    settings = Settings()
    storage = RedisStorage[str](settings)

    content_id_1 = "test_content_1"
    content_1 = "<html><body>Test Content 1</body></html>"
    content_id_2 = "test_content_2"
    content_2 = "<html><body>Test Content 2</body></html>"
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.delete(f"str:{content_id_1}")
    r.delete(f"str:{content_id_2}")

    # Insert the content into Redis
    r.set(f"str:{content_id_1}", content_1)
    r.set(f"str:{content_id_2}", content_2)

    # Now scan it
    scanned_content = list(storage.scan())

    assert len(scanned_content) == 2, "Expected 2 items to be scanned"
    assert content_1 in scanned_content, f"Expected '{content_1}' to be scanned"
    assert content_2 in scanned_content, f"Expected '{content_2}' to be scanned"
    r.delete(f"str:{content_id_1}")
    r.delete(f"str:{content_id_2}")


def test_redis_scan_dict():
    """Test the scan method of RedisStorage with a dictionary."""

    # given
    settings = Settings()
    storage = RedisStorage[dict](settings)

    content_id_1 = "test_content_dict_1"
    content_1 = {"key": "value1", "another_key": "another_value1"}
    content_id_2 = "test_content_dict_2"
    content_2 = {"key": "value2", "another_key": "another_value2"}
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.json().delete(f"dict:{content_id_1}")
    r.json().delete(f"dict:{content_id_2}")

    # Insert the content into Redis
    r.json().set(f"dict:{content_id_1}", Path.root_path(), content_1)
    r.json().set(f"dict:{content_id_2}", Path.root_path(), content_2)

    # Now scan it
    scanned_content = list(storage.scan())

    assert len(scanned_content) == 2, "Expected 2 items to be scanned"
    assert content_1 in scanned_content, f"Expected {content_1} to be scanned"
    assert content_2 in scanned_content, f"Expected {content_2} to be scanned"

    r.json().delete(f"dict:{content_id_1}")
    r.json().delete(f"dict:{content_id_2}")


def test_redis_query():
    """Test the query method of RedisStorage."""

    # given
    settings = Settings()
    storage = RedisStorage[dict](settings)

    content_id_1 = "test_content_dict_1"
    content_1 = {"name": "Alice", "permalink": "http://example.com/alice", "age": 30}
    content_id_2 = "test_content_dict_2"
    content_2 = {"name": "Bob", "permalink": "http://example.com/bob", "age": 40}
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.json().delete(f"dict:{content_id_1}")
    r.json().delete(f"dict:{content_id_2}")

    # Insert the content into Redis
    r.json().set(f"dict:{content_id_1}", Path.root_path(), content_1)
    r.json().set(f"dict:{content_id_2}", Path.root_path(), content_2)

    # Now query it
    queried_content = storage.query(
        permalink="http://example.com/alice",
    )

    assert len(queried_content) == 1
    assert (
        queried_content[0] == content_1
    ), f"Expected {content_1}, but got {queried_content[0]}"

    r.json().delete(f"dict:{content_id_1}")
    r.json().delete(f"dict:{content_id_2}")
