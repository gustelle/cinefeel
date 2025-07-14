from pathlib import Path
from typing import Generator, Protocol, Sequence, runtime_checkable


class StorageError(Exception):
    """Base class for all storage exceptions."""

    pass


@runtime_checkable
class IStorageHandler[U](Protocol):

    # TODO; move this to an implementation
    # this should not be in the interface
    persistence_directory: Path

    # the type of the entity being stored
    # e.g. Film or Person
    entity_type: U

    def insert(self, content_id: str, content: U, *args, **kwargs) -> None:
        """Saves the given content to a persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def insert_many(self, contents: Sequence[U], *args, **kwargs) -> None:
        """Saves multiple contents to persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def select(self, content_id: str, *args, **kwargs) -> U:
        """Loads a content from persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def query(self, *args, **kwargs) -> Sequence[U]:
        """query contents corresponding to the given criteria."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def scan(self, *args, **kwargs) -> Generator[U, None, None]:
        """Scans the persistent storage and returns a list of all contents."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def update(self, content: U, *args, **kwargs) -> U:
        """Updates an existing content in persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")
