from pathlib import Path

import duckdb
from loguru import logger
from pydantic import ValidationError

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler, StorageError
from src.settings import Settings


class JSONEntityStorageHandler[T: Film | Person](IStorageHandler[T, dict]):
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
        """Saves the given content to a file."""

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
                file.write(content.model_dump_json())

        except Exception as e:
            logger.exception(f"Error saving content {content_id}: {e}")
            raise StorageError(f"Error saving {self.entity_type} to {path}") from e

    def select(self, content_id: str) -> T | None:
        """Loads data from a file."""

        try:
            path = self.persistence_directory / f"{content_id}.json"

            with open(path, "r") as file:
                woa = self.entity_type.model_validate_json(file.read())
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
        """Lists entities in the persistent storage corresponding to the given criteria."""

        try:

            logger.debug(
                f"Querying {self.entity_type.__name__}s with order_by='{order_by}', after='{after}', limit={limit}"
            )

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
                logger.warning(
                    f"No {self.entity_type} found matching the criteria: {order_by}, {after}, {limit}"
                )
                return []

            return [self.entity_type(**dict(row)) for row in results.to_dict("records")]

        except duckdb.IOException:
            logger.warning(
                f"Path '{self.persistence_directory}' does not seem to contain anything"
            )
            return []

        except (ValidationError, duckdb.ProgrammingError) as e:
            import traceback

            logger.error(traceback.format_exc())
            raise StorageError(f"Error validating film data: {e}") from e

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise StorageError(f"Error querying films: {e}") from e


# TODO: remove these classes if not needed
class JSONFilmStorageHandler(JSONEntityStorageHandler[Film]):
    pass


class JSONPersonStorageHandler(JSONEntityStorageHandler[Person]):
    pass
