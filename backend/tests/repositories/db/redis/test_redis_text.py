import pytest
import redis

from src.repositories.db.redis.text import RedisTextStorage
from src.settings import Settings


@pytest.fixture(scope="function", autouse=True)
def cleanup_redis(test_settings: Settings):
    """Cleans up the Redis database used for testing."""
    r = redis.Redis(
        host=test_settings.redis_storage_dsn.host,
        port=test_settings.redis_storage_dsn.port,
        db=(
            test_settings.redis_storage_dsn.path.lstrip("/")
            if test_settings.redis_storage_dsn.path
            else 0
        ),
        username=test_settings.redis_storage_dsn.username,
        password=test_settings.redis_storage_dsn.password,
        decode_responses=True,
    )
    r.flushdb()
    yield
    r.flushdb()


def test_redis_text_insert_string(test_settings: Settings):
    """Test the insert method of RedisTextStorage."""

    settings = test_settings
    storage = RedisTextStorage(settings)

    content_id = "test_content"
    content = "<html><body>Test Content</body></html>"

    # make sure the content does not already exist
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )

    # when
    storage.insert(content_id, content)

    # then
    stored_content = r.get(storage._get_key(content_id))

    assert (
        stored_content == content
    ), f"Expected '{content}', but got '{stored_content}'"


def test_redis_text_select(test_settings: Settings):
    """Test the select method of RedisTextStorage."""

    # given
    settings = test_settings
    storage = RedisTextStorage(settings)

    content_id = "test_content"
    content = "<html><body>Test Content</body></html>"
    r = redis.Redis(
        host=settings.redis_storage_dsn.host,
        port=settings.redis_storage_dsn.port,
        decode_responses=True,
    )

    # Insert the content into Redis
    r.set(storage._get_key(content_id), content)

    # Now select it
    retrieved_content = storage.select(content_id)

    assert (
        retrieved_content == content
    ), f"Expected '{content}', but got '{retrieved_content}'"


def test_redis_text_scan(test_settings: Settings):
    """Test the scan method of RedisTextStorage."""

    # given
    settings = test_settings
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

    # Insert the content into Redis
    r.set(storage._get_key(content_id_1), content_1)
    r.set(storage._get_key(content_id_2), content_2)

    # Now scan it
    scanned_content = list(storage.scan())

    assert len(scanned_content) == 2, "Expected 2 items to be scanned"
    assert (
        content_id_1,
        content_1,
    ) in scanned_content, f"Expected '{content_id_1}' to be scanned"
    assert (
        content_id_2,
        content_2,
    ) in scanned_content, f"Expected '{content_id_2}' to be scanned"
