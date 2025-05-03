from typing import Sequence

from entities.film import WikipediaFilm


class IDocumentIndexer:
    """
    Interface for indexing documents.
    """

    def add_documents(self, docs: Sequence[WikipediaFilm], *args, **kwargs) -> None:
        """
        Index a document.

        Args:
            document (str): The document to index.
        """
        raise NotImplementedError("Subclasses should implement this method.")
