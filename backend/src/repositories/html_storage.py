from pathlib import Path
from typing import Generator

from loguru import logger

from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class HtmlContentStorageHandler(IStorageHandler):
    """
    A class to handle persistent storage of raw content.

    TODO:
    - take into account the content type (e.g. film, person) when saving
    - add a mechanism to delete old content
    - testing
    """

    path: Path

    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)

    def insert(self, content_id: str, content: str) -> None:
        """Saves the given data to a file."""

        # TODO
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

    def select(self, content_id: str) -> str:
        """Loads data from a file."""

        # TODO
        try:
            path = self.path / f"{content_id}.html"
            with open(path, "r") as file:
                return file.read()
        except Exception as e:
            logger.info(f"Error loading '{path}': {e}")
            return None

    def scan(self) -> Generator[str, None, None]:
        """Scans the persistent storage and iterates over contents."""

        # TODO
        try:
            for file in self.path.iterdir():
                if file.is_file() and file.suffix == ".html":
                    with open(file, "r") as f:
                        yield f.read()

        except Exception as e:
            logger.info(f"Error scanning '{self.path}': {e}")
            return []


class RawFilmStorageHandler(HtmlContentStorageHandler):

    def __init__(self, settings: Settings):
        super().__init__(settings.persistence_directory / "films" / "raw")


class RawPersonStorageHandler(HtmlContentStorageHandler):

    def __init__(self, settings: Settings):
        super().__init__(settings.persistence_directory / "persons" / "raw")
