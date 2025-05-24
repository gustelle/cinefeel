from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler


class StubStorage[T: Film | Person](IStorageHandler[T, str]):
    """
    handles storage and retrieval of HTML files on disk.
    """

    is_inserted: bool = False

    def insert(
        self,
        content_id: str,
        content: str,
    ) -> None:
        """Saves the given data to a file."""

        self.is_inserted = True
