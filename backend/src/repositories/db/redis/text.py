from typing import Generator, Sequence

import redis
from loguru import logger

from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class RedisTextStorage(IStorageHandler[str]):
    """
    Stores raw text data in Redis.

    Such data keys are prefixed with `raw:`.
    """

    client: redis.Redis

    entity_type: str
    key_prefix: str = "raw"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = redis.Redis(
            host=settings.redis_storage_dsn.host,
            port=settings.redis_storage_dsn.port,
            db=(
                settings.redis_storage_dsn.path.lstrip("/")
                if settings.redis_storage_dsn.path
                else 0
            ),
            username=settings.redis_storage_dsn.username,
            password=settings.redis_storage_dsn.password,
            decode_responses=True,
        )
        logger.info(
            f"Connected to Redis at {settings.redis_storage_dsn.host}:{settings.redis_storage_dsn.port}, db={settings.redis_storage_dsn.path.lstrip('/') if settings.redis_storage_dsn.path else 0}"
        )

    def _get_key(self, content_id: str) -> str:
        """Constructs the Redis key for the given content ID."""
        return f"{self.key_prefix}:{content_id}"

    def _get_content_id(self, key: str) -> str:
        """Extracts the content ID from the Redis key."""
        return key.split(":", 1)[1] if ":" in key else key

    def insert(
        self,
        content_id: str,
        content: str,
    ) -> None:
        """Saves the given data to a file."""

        try:
            key = self._get_key(content_id)

            self.client.set(key, content)

            logger.info(f"Saved '{key}' to Redis storage.")

        except Exception as e:
            logger.error(f"Error saving '{content_id}': {e}")

    def select(
        self,
        content_id: str,
    ) -> str | None:
        """Loads data from a file."""

        try:
            return self.client.get(self._get_key(content_id))
        except Exception as e:
            logger.error(f"Error loading '{content_id}': {e}")
            return None

    def scan(self) -> Generator[tuple[str, str], None, None]:
        """Scans the persistent storage and iterates over contents.

        TODO:
        - testing of the key retrieval

        Example:
        ```python
            for key, content in storage.scan():
                print(content)

            # This will match all HTML files in the storage directory.
            <html>...</html>
            <html>...</html>

        ```

        Returns:
            Generator[str, None, None]: a generator of HTML contents.
        """

        try:

            for key in self.client.scan_iter(match=f"{self.key_prefix}:*"):
                yield self._get_content_id(key), self.client.get(key)

        except Exception as e:
            logger.error(f"Error scanning redis: {e}")
            return []

    def query(
        self,
        *args,
        **kwargs,
    ) -> Sequence[str]:
        raise NotImplementedError(
            "Querying is not supported for RedisTextStorage. Use scan() instead."
        )

    def insert_many(
        self,
        contents: Sequence[str],
        *args,
        **kwargs,
    ) -> None:
        raise NotImplementedError(
            "Bulk insert is not supported for RedisTextStorage. Use insert() instead."
        )

    def update(
        self,
        content: str,
        *args,
        **kwargs,
    ) -> str:
        raise NotImplementedError(
            "Update is not supported for RedisTextStorage. Use insert() instead."
        )
