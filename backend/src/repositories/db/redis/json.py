import hashlib
from typing import Generator, Sequence

import redis
from loguru import logger
from redis.commands.json.path import Path
from redis.commands.search.field import NumericField, TagField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import NumericFilter, Query

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class RedisJsonStorage[U: Composable](IStorageHandler[U]):
    """
    Dumps and loads JSON-serializable entities to/from redis-like databases.
    DB used must support the `redis` client's JSON commands.

    Such data keys are prefixed with `json:`.
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
            # delete if existing
            self.client.ft(self.search_index_name).dropindex(delete_documents=False)
        except Exception as e:
            logger.warning(f"Error deleting index for Redis: {e}")

        try:
            self.client.ft(self.search_index_name).create_index(
                (
                    TagField("$.permalink", as_name="permalink"),
                    NumericField(
                        "$.uid_hash", as_name="uid_hash", sortable=True
                    ),  # used for sorting
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
        """Generates a numeric hash for the UID of the content.

        nevermind the value of the hash compared to the film title, it's just a way to have a sortable numeric value.
        The uid_hash must only be stable and unique for each uid.
        """

        sha1 = hashlib.sha1()
        sha1.update(str.encode(content.uid))
        hash_as_hex = sha1.hexdigest()
        # convert the hex back to int and restrict it to the relevant int range
        seed = int(hash_as_hex, 16) % 4294967295  # 2^32 -1

        return seed % (10**8)

    def insert(
        self,
        content_id: str,
        content: U,
    ) -> None:

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

        except Exception as e:
            logger.error(f"Error saving '{content_id}': {e}")

    def insert_many(
        self,
        contents: Sequence[U],
    ) -> None:

        for content in contents:
            self.insert(content_id=content.uid, content=content)

    def select(
        self,
        content_id: str,
    ) -> U | None:

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

        Returns:
            Generator[U, None, None]: a generator of documents of type U
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
        after: U | None = None,
        **kwargs,
    ) -> Sequence[U]:
        """
        @see: https://redis.io/docs/latest/develop/clients/redis-py/queryjson/
        """

        if permalink is not None:
            q = f"@permalink:{{'{permalink}'}}"

        else:
            q = "*"

        if after:
            min_uid = self._get_uid_hash(after)
            query = Query(q).add_filter(
                NumericFilter(
                    "uid_hash",
                    minval=min_uid,
                    minExclusive=True,
                    maxval="+inf",
                )
            )
        else:
            query = Query(q)

        results = self.client.ft(self.search_index_name).search(
            query.paging(0, limit).sort_by("uid_hash", asc=True)
        )

        return [
            self.entity_type.model_validate_json(doc.json, by_name=True)
            for doc in results.docs
        ][:limit]
