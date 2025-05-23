import glob
from pathlib import Path
from typing import Generator

from loguru import logger

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler


class HtmlContentStorageHandler[T: Film | Person](IStorageHandler[T, str]):
    """
    handles storage and retrieval of HTML files on disk.

    TODO:
    - add a mechanism to delete old content
    - testing
    """

    path: Path

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type

        logger.debug(
            f"Created class '{new_cls.__name__}' with entity type '{new_cls.entity_type}'"
        )

        return new_cls

    def __init__(self, path: Path):

        # entity_type is set by the generic type in the class definition
        # see `IStorageHandler.__class_getitem__`
        self.path = path / "html" / self.entity_type.__name__.lower()
        self.path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created dir '{self.path}'")

    def insert(
        self,
        content_id: str,
        content: str,
    ) -> None:
        """Saves the given data to a file."""

        try:
            path = self.path / f"{content_id}.html"

            # overwrite if exists
            if path.exists():
                path.unlink()

            with open(path, "w") as file:
                file.write(content)

            # logger.info(f"Saved '{content_id}' ")

        except Exception as e:
            logger.info(f"Error saving '{content_id}': {e}")

    def select(
        self,
        content_id: str,
    ) -> str:
        """Loads data from a file."""

        try:
            path = self.path / f"{content_id}.html"
            with open(path, "r") as file:
                return file.read()
        except Exception as e:
            logger.info(f"Error loading '{path}': {e}")
            return None

    def scan(
        self, file_pattern: str = "*"  # match all files,
    ) -> Generator[str, None, None]:
        """Scans the persistent storage and iterates over contents.

        Args:
            file_pattern (str, optional): a filename pattern to match. Defaults to None.

        Returns:
            Generator[str, None, None]: a generator of HTML contents.
        """

        logger.info(f"Scanning '{self.path}' for pattern '{file_pattern}'")

        try:

            file_path = self.path / f"{file_pattern}.html"
            for file in glob.glob(str(file_path)):
                with open(file, "r") as f:
                    yield f.read()

        except Exception as e:
            logger.info(f"Error scanning '{self.path}': {e}")
            return []
