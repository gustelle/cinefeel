from src.entities.movie import Movie
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler


class StubStorage[T: Movie | Person](IStorageHandler[T]):
    """
    handles storage and retrieval of HTML files on disk.
    """

    is_inserted: bool = False

    def insert(
        self,
        content_id: str,
        content: T,
        *args,
    ) -> None:
        """Saves the given data to a file."""

        self.is_inserted = True

    def insert_many(
        self,
        contents: list[T],
    ) -> None:
        """Saves multiple contents to persistent storage."""

        self.is_inserted = True
