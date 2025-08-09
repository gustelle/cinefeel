import unicodedata
from typing import Generator, Sequence

import redis
from loguru import logger
from redis.commands.json.path import Path
from redis.commands.search.field import NumericField, TagField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class RedisJsonStorage[U: Composable](IStorageHandler[U]):
    """
    Supports `str` and `dict` types for Redis storage.
    """

    client: redis.Redis
    key_prefix: str = "json"
    search_index_name: str = "idx:entities"
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

        try:
            self.client.ft(self.search_index_name).create_index(
                (
                    TagField("$.uid", as_name="uid"),
                    TagField("$.permalink", as_name="permalink"),
                    TextField("$.title", as_name="title"),
                    NumericField("$.uid_hash", as_name="uid_hash"),  # used for sorting
                ),
                definition=IndexDefinition(
                    prefix=[f"{self.key_prefix}:"], index_type=IndexType.JSON
                ),
            )
        except Exception as e:
            logger.error(f"Error creating index for Redis: {e}")

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """

        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type
        return new_cls

    def _get_key(self, content_id: str) -> str:
        """Generates the Redis key for the given content ID."""
        return f"{self.key_prefix}:{self.entity_type.__name__}-{content_id}"

    def _get_uid_hash(self, content: U) -> int:
        """Generates a numeric hash for the UID of the content."""
        # Convertir la chaîne en minuscules pour uniformiser
        s = (
            unicodedata.normalize("NFKD", content.uid.lower())
            .encode("ASCII", "ignore")
            .decode()
        )
        # Convertir chaque caractère en son rang dans l'alphabet
        return int("".join(str(ord(char)) for char in s))

    def insert(
        self,
        content_id: str,
        content: U,
    ) -> None:
        """Saves the given data to a file."""

        try:
            key = self._get_key(content_id)

            data = content.model_dump(mode="json")
            data["uid_hash"] = self._get_uid_hash(content)  # Store the hash for sorting

            # Store the content as a JSON object in Redis
            self.client.json().set(
                key,
                Path.root_path(),
                data,
            )

            logger.debug(data)

        except Exception as e:
            logger.error(f"Error saving '{content_id}': {e}")

    def insert_many(
        self,
        contents: Sequence[U],
    ) -> None:
        """Saves multiple contents to persistent storage."""

        for content in contents:
            self.insert(content_id=content.uid, content=content)

        logger.info(f"Inserted {len(contents)} items into Redis storage.")

    def select(
        self,
        content_id: str,
    ) -> U | None:
        """Loads data from a file."""

        try:

            # Load the content as a JSON object from Redis
            body = self.client.json().get(self._get_key(content_id))

            body.pop("uid_hash", None)  # Remove the hash field if it exists

            return self.entity_type.model_validate(body, by_name=True) if body else None

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

            for key in self.client.scan_iter(match=f"{self.key_prefix}:*"):

                try:
                    data = self.client.json().get(key)
                    data.pop("uid_hash", None)  # Remove the hash field if it exists
                    yield self.entity_type.model_validate(data, by_name=True)
                except Exception as e:
                    logger.error(f"Error parsing JSON from key '{key}': {e}")
                    continue

        except Exception as e:
            logger.error(f"Error scanning redis: {e}")
            return []

    def query(
        self,
        permalink: str | None = None,
        limit: int = 100,
        order_by: str = "uid",
        after: U | None = None,
    ) -> Sequence[U]:
        """Lists entities in the persistent storage corresponding to the given criteria."""

        if order_by not in ["uid", "permalink", "title"]:
            raise ValueError(
                f"Unsupported order_by field: {order_by}, supported fields are: uid, permalink, title"
            )

        if permalink is not None:
            q = f"@permalink:{{'{permalink}'}}"

        else:
            if after is None:
                q = "*"
            else:
                uid_hash = self._get_uid_hash(after) + 1
                q = f"@uid_hash:[{uid_hash} +inf]"

        logger.debug(f"Querying Redis with: {q}, order_by: {order_by}, limit: {limit}")

        results = (
            self.client.ft(self.search_index_name)
            .search(Query(q).sort_by(order_by, asc=True))
            .docs
        )

        logger.debug(f"Found {len(results)} results for query: {q}")

        return [
            self.entity_type.model_validate_json(doc.json, by_name=True)
            for doc in results
        ][:limit]
