# TODO:
# redis storage of html content
from typing import Generator, Type

import redis
from loguru import logger

from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class RedisTextStorage(IStorageHandler[str]):
    """
    handles storage and retrieval of HTML files on disk.
    """

    entity_type: Type[str] = str
    client: redis.Redis

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

    def insert(
        self,
        content_id: str,
        content: str,
    ) -> None:
        """Saves the given data to a file."""

        try:
            # Store the content in Redis
            self.client.set(content_id, content)

        except Exception as e:
            logger.error(f"Error saving '{content_id}': {e}")

    def select(
        self,
        content_id: str,
    ) -> str:
        """Loads data from a file."""

        try:
            return self.client.get(content_id)
        except Exception as e:
            logger.error(f"Error loading '{content_id}': {e}")
            return None

    def scan(self, file_pattern: str = "*.html") -> Generator[str, None, None]:
        """Scans the persistent storage and iterates over contents.

        Args:
            file_pattern (str, optional): a filename pattern to match. Defaults to `*.html`
                This is a glob pattern, so it can be used to match multiple files.

        Example:
        ```python
            for content in storage.scan("*.html"):
                print(content)

            # This will match all HTML files in the storage directory.
            <html>...</html>
            <html>...</html>

        ```

        Returns:
            Generator[str, None, None]: a generator of HTML contents.
        """

        try:

            for key in self.client.scan_iter():
                yield self.client.get(key)

        except Exception as e:
            logger.error(f"Error scanning '{self.path}': {e}")
            return []
