from pathlib import Path
from typing import Generator, Protocol


class IStorageHandler[T](Protocol):

    persistence_directory: Path

    def insert(self, o: T, *args, **kwargs) -> None:
        """Saves the given film to a persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def select(self, id: str, *args, **kwargs) -> T:
        """Loads a film from persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def query(self, *args, **kwargs) -> list[T]:
        """query films corresponding to the given criteria."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def scan(self, *args, **kwargs) -> Generator[T, None, None]:
        """Scans the persistent storage and returns a list of all films."""
        raise NotImplementedError("This method should be overridden by subclasses.")
