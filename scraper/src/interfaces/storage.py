from pathlib import Path
from typing import Protocol

from entities.film import Film


class IStorageHandler(Protocol):

    persistence_directory: Path

    def insert(self, film: Film, *args, **kwargs) -> None:
        """Saves the given film to a persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def select(self, *args, **kwargs) -> Film:
        """Loads a film from persistent storage."""
        raise NotImplementedError("This method should be overridden by subclasses.")

    def query(self, *args, **kwargs) -> list[Film]:
        """query films corresponding to the given criteria."""
        raise NotImplementedError("This method should be overridden by subclasses.")
