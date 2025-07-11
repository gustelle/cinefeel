from pathlib import Path

import duckdb
import orjson
from loguru import logger
from pydantic import ValidationError

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler, StorageError
from src.settings import Settings


class JSONEntityStorageHandler[T: Film | Person](IStorageHandler[T]):
    """
    handles persistence of `Film` or `Person` objects into JSON files.
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

        if self.entity_type is Film:
            self.persistence_directory = settings.persistence_directory / "films"
        elif self.entity_type is Person:
            self.persistence_directory = settings.persistence_directory / "persons"
        else:
            raise ValueError(
                f"Unsupported entity type: {self.entity_type}. "
                "Expected Film or Person."
            )

        self.persistence_directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created dir '{self.persistence_directory}'")

    def insert(
        self,
        content_id: str,
        content: T,
    ) -> None:
        """Saves the given content to a file.

        Raises StorageError: so that the caller can log and handle it gracefully.
        """

        path = self.persistence_directory / f"{content_id}.json"

        try:

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
                woa = self.entity_type.model_construct(**orjson.loads(file.read()))
                return woa
        except Exception as e:
            logger.exception(f"Error loading film from {path}: {e}")
            return None

    def query(
        self,
        order_by: str = "uid",
        after: T | None = None,
        limit: int = 100,
    ) -> list[T]:
        """Lists entities in the persistent storage corresponding to the given criteria.

        Fixed: same as `select`, we go through `model_construct` to avoid uid validation issues.
        """

        try:

            results = (
                duckdb.sql(
                    f"SELECT * FROM read_json_auto('{str(self.persistence_directory)}/*.json')"
                )
                .filter(f"uid > '{after.uid}'" if after else "1=1")
                .limit(limit)
                .order(order_by)
                .to_df()
            )

            if results.empty:
                logger.warning(f"No {self.entity_type} found matching the criteria")
                return []

            return [
                # use model_construct to avoid uid validation issues
                self.entity_type.model_construct(**dict(row))
                for row in results.to_dict("records")
            ]

        except duckdb.IOException:
            logger.warning(
                f"Path '{self.persistence_directory}' does not seem to contain anything"
            )
            return []

        except (ValidationError, duckdb.ProgrammingError) as e:
            import traceback

            logger.error(traceback.format_exc())
            raise StorageError(f"Error validating data: {e}") from e

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise StorageError(f"Error querying data: {e}") from e
