import glob
from pathlib import Path
from typing import Generator

from loguru import logger

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler


class LocalTextStorage[T: Film | Person](IStorageHandler[T, str]):
    """
    handles storage and retrieval of HTML files on disk.
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

        if not hasattr(self, "entity_type"):
            raise ValueError(
                "LocalTextStorage must be initialized with a generic type."
            )

        # entity_type is set by the generic type in the class definition
        # see `IStorageHandler.__class_getitem__`
        self.path = path / "html" / self.entity_type.__name__.lower()
        self.path.mkdir(parents=True, exist_ok=True)

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

        except Exception as e:
            logger.error(f"Error saving '{content_id}': {e}")

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
            logger.error(f"Error loading '{path}': {e}")
            return None

    def scan(self, file_pattern: str = "*.html") -> Generator[str, None, None]:
        """Scans the persistent storage and iterates over contents.

        Args:
            file_pattern (str, optional): a filename pattern to match. Defaults to `*.html`
                This is a glob pattern, so it can be used to match multiple files.

        Example:
        ```python
            for content in storage.scan("*.html"):
                print(content)

            # This will match all HTML files in the storage directory.
            <html>...</html>
            <html>...</html>

        ```

        Returns:
            Generator[str, None, None]: a generator of HTML contents.
        """

        try:

            file_path = self.path / file_pattern
            for file in glob.glob(str(file_path)):
                with open(file, "r") as f:
                    yield f.read()

        except Exception as e:
            logger.error(f"Error scanning '{self.path}': {e}")
            return []
