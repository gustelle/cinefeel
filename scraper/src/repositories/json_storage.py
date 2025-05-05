from pathlib import Path

import duckdb
import orjson
from entities.film import Film
from interfaces.storage import IStorageHandler
from settings import Settings


class JsonStorageHandler(IStorageHandler):
    """
    A class to handle file persistence.

    TODO:
        - usage of DuckDB
        - testing
    """

    film_dir: Path
    persons_dir: Path

    def __init__(self, settings: Settings):
        self.film_dir = settings.persistence_directory / "films"
        self.persons_dir = settings.persistence_directory / "persons"
        self.film_dir.mkdir(parents=True, exist_ok=True)
        self.persons_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directories '{self.film_dir}' and '{self.persons_dir}'")

    def insert(self, film: Film) -> None:
        """Saves the given data to a file."""

        # TODO
        try:
            path = self.film_dir / f"{film.uid}.json"

            # overwrite if exists
            if path.exists():
                path.unlink()

            with open(path, "wb") as file:
                file.write(orjson.dumps(film.model_dump(mode="json")))
        except Exception as e:
            print(f"Error saving film {film}: {e}")

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
        after_film: Film | None = None,
        limit: int = 100,
    ) -> list[Film]:
        """Lists films in the persistent storage corresponding to the given criteria."""

        results = (
            duckdb.sql(f"SELECT * FROM read_json_auto('{str(self.film_dir)}/*.json')")
            .filter(f"uid > '{after_film.uid}'" if after_film else "1=1")
            .limit(limit)
            .order(order_by)
            .to_df()
        )

        if results.empty:
            print(
                f"No films found matching the criteria: {order_by}, {after_film}, {limit}"
            )
            return []

        return [Film.model_validate(dict(row)) for row in results.to_dict("records")]
