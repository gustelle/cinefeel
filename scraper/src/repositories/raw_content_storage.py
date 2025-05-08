from pathlib import Path

from interfaces.storage import IStorageHandler
from settings import Settings


class HtmlContentStorageHandler(IStorageHandler):
    """
    A class to handle persistent storage of raw content.

    TODO:
        - testing
    """

    path: Path

    def __init__(self, path: Path):
        self.path = path
        self.path.mkdir(parents=True, exist_ok=True)
        print(f"Created directories '{self.path}'")

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

            # print(f"Saved '{content_id}' ")

        except Exception as e:
            print(f"Error saving '{content_id}': {e}")

    def select(self, content_id: str) -> str:
        """Loads data from a file."""

        # TODO
        try:
            path = self.path / f"{content_id}.html"
            with open(path, "r") as file:
                return file.read()
        except Exception as e:
            print(f"Error loading '{path}': {e}")
            return None


class RawFilmStorageHandler(HtmlContentStorageHandler):

    def __init__(self, settings: Settings):
        super().__init__(settings.persistence_directory / "films" / "raw")


class RawPersonStorageHandler(HtmlContentStorageHandler):

    def __init__(self, settings: Settings):
        super().__init__(settings.persistence_directory / "persons" / "raw")
