import redis

from src.repositories.db.redis import RedisTextStorage
from src.settings import Settings


def test_redis_insert():
    """Test the insert method of RedisTextStorage."""

    settings = Settings()
    storage = RedisTextStorage(settings)

    content_id = "test_content"
    content = "<html><body>Test Content</body></html>"

    # make sure the content does not already exist
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.delete(content_id)  # Clear any existing content with the same ID

    # when
    storage.insert(content_id, content)

    # then
    stored_content = r.get(content_id)

    assert (
        stored_content == content
    ), f"Expected '{content}', but got '{stored_content}'"
    r.delete(content_id)


def test_redis_select():
    """Test the select method of RedisTextStorage."""

    # given
    settings = Settings()
    storage = RedisTextStorage(settings)

    content_id = "test_content"
    content = "<html><body>Test Content</body></html>"
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )

    r.delete(content_id)

    # Insert the content into Redis
    r.set(content_id, content)

    # Now select it
    retrieved_content = storage.select(content_id)

    assert (
        retrieved_content == content
    ), f"Expected '{content}', but got '{retrieved_content}'"
    r.delete(content_id)


def test_redis_scan():
    """Test the scan method of RedisTextStorage."""

    # given
    settings = Settings()
    storage = RedisTextStorage(settings)

    content_id_1 = "test_content_1"
    content_1 = "<html><body>Test Content 1</body></html>"
    content_id_2 = "test_content_2"
    content_2 = "<html><body>Test Content 2</body></html>"
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )
    r.delete(content_id_1)
    r.delete(content_id_2)

    # Insert the content into Redis
    r.set(content_id_1, content_1)
    r.set(content_id_2, content_2)

    # Now scan it
    scanned_content = list(storage.scan())

    assert len(scanned_content) == 2, "Expected 2 items to be scanned"
    assert content_1 in scanned_content, f"Expected '{content_1}' to be scanned"
    assert content_2 in scanned_content, f"Expected '{content_2}' to be scanned"
    r.delete(content_id_1)
    r.delete(content_id_2)
