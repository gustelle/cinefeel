from pathlib import Path
from typing import Generator, Protocol, runtime_checkable

from src.entities.film import Film
from src.entities.person import Person


class StorageError(Exception):
    """Base class for all storage exceptions."""

    pass


@runtime_checkable
class IStorageHandler[U: Film | Person, V: bytes | str | dict](Protocol):

    # TODO; move this to an implementation
    # this should not be in the interface
    persistence_directory: Path

    # the type of the entity being stored
    # e.g. Film or Person
    entity_type: U

    def insert(self, content_id: str, content: V, *args, **kwargs) -> None:
        """Saves the given content to a persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def select(self, content_id: str, *args, **kwargs) -> V:
        """Loads a content from persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def query(self, *args, **kwargs) -> list[V]:
        """query contents corresponding to the given criteria."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def scan(self, *args, **kwargs) -> Generator[V, None, None]:
        """Scans the persistent storage and returns a list of all contents."""
        raise NotImplementedError("This method should be overridden by subclasses.")
