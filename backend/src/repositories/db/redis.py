from typing import Generator, Sequence

import redis
from loguru import logger
from redis.commands.json.path import Path
from redis.commands.search.field import TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class RedisStorage[U: str | dict](IStorageHandler[U]):
    """
    Supports `str` and `dict` types for Redis storage.
    """

    client: redis.Redis
    entity_type: type[U]

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

        if self.entity_type is dict:
            # create index for JSON storage
            schema = (TagField("$.permalink", as_name="permalink"),)
            self.client.ft("idx:entities").create_index(
                schema,
                definition=IndexDefinition(prefix=["dict:"], index_type=IndexType.JSON),
            )

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """

        if generic_type not in (str, dict):
            raise TypeError(
                "RedisStorage only supports 'str' or 'dict' types for storage."
            )

        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type
        return new_cls

    def insert(
        self,
        content_id: str,
        content: U,
    ) -> None:
        """Saves the given data to a file."""

        try:
            key = f"{self.entity_type.__name__}:{content_id}"
            if self.entity_type is dict:
                # Store the content as a JSON object in Redis
                self.client.json().set(
                    key,
                    Path.root_path(),
                    content,
                )
            else:
                # Store the content in Redis
                self.client.set(key, content)

            logger.info(f"Saved '{key}' to Redis storage.")

        except Exception as e:
            logger.error(f"Error saving '{content_id}': {e}")

    def select(
        self,
        content_id: str,
    ) -> U | None:
        """Loads data from a file."""

        try:
            if self.entity_type is dict:
                # Load the content as a JSON object from Redis
                return self.client.json().get(
                    f"{self.entity_type.__name__}:{content_id}"
                )
            else:
                return self.client.get(f"{self.entity_type.__name__}:{content_id}")
        except Exception as e:
            logger.error(f"Error loading '{content_id}': {e}")
            return None

    def scan(self) -> Generator[U, None, None]:
        """Scans the persistent storage and iterates over contents.

        Example:
        ```python
            for content in storage.scan():
                print(content)

            # This will match all HTML files in the storage directory.
            <html>...</html>
            <html>...</html>

        ```

        Returns:
            Generator[str, None, None]: a generator of HTML contents.
        """

        try:

            if self.entity_type is dict:
                # Scan for all JSON objects in Redis
                for key in self.client.scan_iter(
                    match=f"{self.entity_type.__name__}:*"
                ):
                    yield self.client.json().get(key)
            else:
                for key in self.client.scan_iter(
                    match=f"{self.entity_type.__name__}:*"
                ):
                    yield self.client.get(key)

        except Exception as e:
            logger.error(f"Error scanning redis: {e}")
            return []

    def query(
        self,
        order_by: str = "uid",
        permalink: str | None = None,
        after: U | None = None,
        limit: int = 100,
    ) -> Sequence[U]:
        """Lists entities in the persistent storage corresponding to the given criteria.

        Fixed: same as `select`, we go through `model_construct` to avoid uid validation issues.
        """
        if self.entity_type is not dict:
            raise NotImplementedError(
                "RedisStorage does not support query for raw strings."
            )

        logger.info("@permalink:{" + permalink + "}")

        results = (
            self.client.ft("idx:entities")
            .search(Query("@permalink:{http://example.com/alice}"))
            .docs
        )

        if not results:
            logger.warning(
                f"No '{self.entity_type.__name__}' found matching the criteria"
            )
            return []
        return [
            self.entity_type.model_validate(dict(doc), by_name=True) for doc in results
        ][:limit]
