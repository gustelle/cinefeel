from pathlib import Path
from typing import Generator

import duckdb
from loguru import logger
from pydantic import ValidationError

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler, StorageError
from src.settings import Settings


class JSONEntityStorageHandler[T: Composable](IStorageHandler[T]):
    """
    handles persistence of `Composable` objects into JSON files on disk.

    This is useful for testing and local development but not for production,
    infrastructure of production should not depend on local disk storage.
    """

    persistence_directory: Path
    entity_type: type[T]

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type

        return new_cls

    def __init__(self, settings: Settings):

        if not hasattr(self, "entity_type"):
            raise ValueError(
                "JSONEntityStorageHandler must be initialized with a generic type."
            )

        self.persistence_directory = (
            settings.local_storage_directory / f"{self.entity_type.__name__.lower()}s"
        )
        self.persistence_directory.mkdir(parents=True, exist_ok=True)

    def insert(
        self,
        content_id: str,
        content: T,
    ) -> None:
        """Saves the given content to a file.

        Raises StorageError: so that the caller can log and handle it gracefully.
        """

        try:

            path = self.persistence_directory / f"{content_id}.json"

            # check if the content is of the expected type
            if not isinstance(content, self.entity_type):
                raise ValueError(
                    f"Unsupported entity type: {type(content)}. "
                    f"Expected {self.entity_type}."
                )

            # overwrite if exists
            if path.exists():
                path.unlink()

            with open(path, "w") as file:
                file.write(content.model_dump_json(exclude_none=True, indent=2))

        except Exception as e:
            logger.exception(f"Error saving content {content_id}: {e}")
            raise StorageError(f"Error saving {self.entity_type} to {path}") from e

    def select(self, content_id: str) -> T | None:
        """Loads data from a file.

        Uses orjson to deserialize the content, to avoid goind through the uid field_validation,
        because if we'd use `model_validate` with a uid serialized as `film_1234`, the uid validation would lead to
        creating a new uid like `film_film_1234`, which is not what we want.
        """

        try:
            path = self.persistence_directory / f"{content_id}.json"

            with open(path, "r") as file:
                # load through orjson to avoid uid validation issues
                woa = self.entity_type.model_validate_json(file.read(), by_name=True)
                return woa
        except Exception as e:
            logger.exception(f"Error loading movie from {path}: {e}")
            return None

    def query(
        self,
        order_by: str = "uid",
        permalink: str | None = None,
        after: T | None = None,
        limit: int = 100,
    ) -> list[T]:
        """Lists entities in the persistent storage corresponding to the given criteria.

        Fixed: same as `select`, we go through `model_construct` to avoid uid validation issues.
        """

        # fix: https://github.com/duckdb/duckdb/issues/13498
        # duckdb.sql is not thread-safe, so we need to use a connection
        conn = duckdb.connect()

        try:

            results = (
                conn.sql(
                    f"SELECT * FROM read_json_auto('{str(self.persistence_directory)}/*.json', union_by_name = true)"
                )
                .filter(f"uid > '{after.uid}'" if after else "1=1")
                .filter(f"permalink = '{permalink}'" if permalink else "1=1")
                .limit(limit)
                .order(order_by)
                .to_df()
            )

            if results.empty:
                logger.warning(
                    f"No '{self.entity_type.__name__}' found matching the criteria"
                )
                return []

            return [
                self.entity_type.model_validate(dict(row), by_name=True)
                for row in results.to_dict("records")
            ]

        except duckdb.IOException:
            logger.warning(
                f"Path '{self.persistence_directory}' does not seem to contain anything"
            )
            return []

        except (ValidationError, duckdb.ProgrammingError) as e:

            raise StorageError(f"Error validating data: {e}") from e

        except Exception as e:

            import traceback

            logger.error(traceback.format_exc())
            raise StorageError(f"Error querying data: {e}") from e
        finally:
            conn.close()

    def scan(self) -> Generator[T, None, None]:
        """Scans the persistent storage and returns an iterator over the contents."""

        try:

            # iterate over all JSON files in the directory
            for file in self.persistence_directory.glob("*.json"):
                with open(file, "r") as f:
                    try:

                        # use model_construct to avoid uid validation issues
                        yield self.entity_type.model_validate_json(
                            f.read(), by_name=True
                        )
                    except ValidationError as e:
                        logger.error(f"Error loading JSON from '{file}': {e}")
                        continue

        except Exception as e:
            logger.error(f"Error scanning storage: {e}")
            raise StorageError(f"Error scanning storage: {e}") from e
