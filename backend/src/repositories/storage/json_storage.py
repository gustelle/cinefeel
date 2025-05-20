from pathlib import Path

import duckdb
import orjson
from loguru import logger

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class JSONEntityStorageHandler[T: Film | Person](IStorageHandler[T, dict]):
    """
    handles persistence of entities into JSON files.
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
        content: dict,
    ) -> None:
        """Saves the given data to a file."""

        try:
            path = self.persistence_directory / f"{content_id}.json"

            # overwrite if exists
            if path.exists():
                path.unlink()

            with open(path, "wb") as file:
                file.write(orjson.dumps(content))

                logger.info(f"Saved {self.entity_type} to {path}")

        except Exception as e:
            logger.info(f"Error saving content {content_id}: {e}")

    def select(self, content_id: str) -> dict:
        """Loads data from a file."""

        try:
            path = self.persistence_directory / f"{content_id}.json"

            with open(path, "rb") as file:
                woa = orjson.loads(file.read())
                return woa
        except Exception as e:
            logger.info(f"Error loading film from {path}: {e}")
            return None

    def query(
        self,
        order_by: str = "uid",
        after: T | None = None,
        limit: int = 100,
    ) -> list[T]:
        """Lists films in the persistent storage corresponding to the given criteria."""

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
            logger.info(
                f"No films found matching the criteria: {order_by}, {after}, {limit}"
            )
            return []

        return [self.entity_type(**dict(row)) for row in results.to_dict("records")]


class JSONFilmStorageHandler(JSONEntityStorageHandler[Film]):
    pass


class JSONPersonStorageHandler(JSONEntityStorageHandler[Person]):
    pass
