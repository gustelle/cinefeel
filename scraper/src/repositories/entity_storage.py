from pathlib import Path
from typing import TypeVar

import duckdb
import orjson

from entities.film import Film
from entities.person import Person
from interfaces.storage import IStorageHandler
from settings import Settings


class EntityStorageHandler[T: (Film, Person)](IStorageHandler[T]):
    """
    A class to handle file persistence for entities.
    """

    persistence_directory: Path
    entity_type: str

    def __init__(self, settings: Settings):

        self.entity_type = self.__orig_class__.__args__[0].__name__.lower()

        self.persistence_directory = (
            settings.persistence_directory / self.entity_type / "analyzed"
        )
        self.persistence_directory.mkdir(parents=True, exist_ok=True)
        print(f"Created dir '{self.persistence_directory}'")

    def insert(self, o: T) -> None:
        """Saves the given data to a file."""

        # TODO
        try:
            path = self.persistence_directory / f"{o.uid}.json"

            # overwrite if exists
            if path.exists():
                path.unlink()

            with open(path, "wb") as file:
                file.write(orjson.dumps(o.model_dump(mode="json")))
        except Exception as e:
            print(f"Error saving film {o}: {e}")

    def select(self, path: Path) -> Film:
        """Loads data from a file."""

        # TODO
        try:
            with open(path, "rb") as file:
                data = orjson.loads(file.read())
                film = Film.model_validate(data)

                return film
        except Exception as e:
            print(f"Error loading film from {path}: {e}")
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
            print(f"No films found matching the criteria: {order_by}, {after}, {limit}")
            return []

        return [T.model_validate(dict(row)) for row in results.to_dict("records")]


class FilmStorageHandler(EntityStorageHandler[Film]):
    pass


class PersonStorageHandler(EntityStorageHandler[Person]):
    pass
