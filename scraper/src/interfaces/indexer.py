from typing import Sequence

from entities.film import Film


class IDocumentIndexer:
    """
    Interface for indexing documents.
    """

    def upsert(self, docs: Sequence[Film], *args, **kwargs) -> None:
        """
        Index a document in the index in upsert mode.
        This means that if the document already exists, it will be updated.
        If it does not exist, it will be created.

        Args:
            docs (Sequence[Film]): A sequence of `Film`s to index.
        """
        raise NotImplementedError("Subclasses should implement this method.")
