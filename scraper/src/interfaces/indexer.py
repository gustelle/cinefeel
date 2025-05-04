from typing import Sequence

from entities.film import Film


class IDocumentIndexer:
    """
    Interface for indexing documents.
    """

    def add_documents(self, docs: Sequence[Film], *args, **kwargs) -> None:
        """
        Index a document.

        Args:
            document (str): The document to index.
        """
        raise NotImplementedError("Subclasses should implement this method.")
