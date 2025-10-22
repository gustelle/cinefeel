from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator, Sequence

from src.entities.composable import Composable
from src.entities.relationship import BaseRelationship


class IStorageHandler[U](ABC):

    # TODO; move this to an implementation
    # this should not be in the interface
    persistence_directory: Path

    # the type of the entity being stored
    # e.g. Movie or Person
    entity_type: U

    @abstractmethod
    def insert(self, content_id: str, content: U, *args, **kwargs) -> None:
        """Saves the given content to a persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    @abstractmethod
    def insert_many(self, contents: Sequence[U], *args, **kwargs) -> None:
        """Saves multiple contents to persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    @abstractmethod
    def select(self, content_id: str, *args, **kwargs) -> U:
        """Loads a content from persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    @abstractmethod
    def query(self, *args, **kwargs) -> Sequence[U]:
        """query contents corresponding to the given criteria."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    @abstractmethod
    def scan(self, *args, **kwargs) -> Generator[tuple[str, U], None, None]:
        """Scans the persistent storage and returns a list of all contents with their IDs.

        Returns:
            Generator[tuple[str, U], None, None]: a generator of tuples (uid, U)
        """
        raise NotImplementedError("This method should be overridden by subclasses.")

    @abstractmethod
    def update(self, content: U, *args, **kwargs) -> U:
        """Updates an existing content in persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")


class IRelationshipHandler[U: Composable](IStorageHandler[U]):

    @abstractmethod
    def add_relationship(
        self,
        relationship: BaseRelationship,
        *args,
        **kwargs,
    ) -> None:
        """Adds a relationship between two contents.

        raises:
            RelationshipError: If the relationship cannot be added.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
