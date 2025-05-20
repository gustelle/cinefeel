from typing import Protocol, Sequence

from src.entities.film import Film
from src.entities.person import Person


class IDocumentIndexer[T: (Film, Person)](Protocol):
    """
    Interface for indexing documents.
    """

    def insert_or_update(self, docs: Sequence[T], *args, **kwargs) -> None:
        """
        Index a document in the index in upsert mode.
        This means that if the document already exists, it will be updated.
        If it does not exist, it will be created.

        Args:
            docs (Sequence[T]): A sequence of `T`s to index, where `T` is a subclass of `Film` or `Person`.
        """
        raise NotImplementedError("Subclasses should implement this method.")
