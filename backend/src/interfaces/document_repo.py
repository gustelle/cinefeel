from typing import Protocol, Sequence

from src.entities.film import Film
from src.entities.person import Person


class IDocumentRepository[T: (Film, Person)](Protocol):
    """
    Interface for storing and retrieving documents
    """

    def setup(self, *args, **kwargs) -> bool:
        """
        Setup the document repository.
        This method should be called before any other method.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def insert_or_update(self, docs: Sequence[T], *args, **kwargs) -> int:
        """
        Index a document in the index in upsert mode.
        This means that if the document already exists, it will be updated.
        If it does not exist, it will be created.

        Args:
            docs (Sequence[T]): A sequence of `T`s to index, where `T` is a subclass of `Film` or `Person`.

        Returns:
            int: The number of documents inserted or updated.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def delete(self, docs: Sequence[T], *args, **kwargs) -> None:
        """
        Delete documents from the repository.

        Args:
            docs (Sequence[T]): A sequence of `T`s to delete, where `T` is a subclass of `Film` or `Person`.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def get(self, doc_id: str, *args, **kwargs) -> T:
        """
        Retrieve a document by its ID.

        Args:
            doc_id (str): The ID of the document to retrieve.

        Returns:
            T: The document with the specified ID.
        """
        raise NotImplementedError("Subclasses should implement this method.")


class IDocumentQuery[T: (Film, Person)](Protocol):
    """
    Interface for querying documents and their related entities.
    """

    def query(self, *args, **kwargs) -> Sequence[T]:
        """query contents corresponding to the given criteria."""
        raise NotImplementedError("This method should be overridden by subclasses.")
