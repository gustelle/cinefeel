from typing import Protocol

from src.interfaces.content_splitter import Section


class ISimilaritySearch(Protocol):
    """
    Class to handle BERT similarity calculations.
    """

    def most_similar(self, query: str, corpus: list[str]) -> str:
        """
        Find the most similar document in the corpus to the given query.

        Args:
            query (str): The query string.
            corpus (list[str]): The list of documents to search.

        Returns:
            str: The most similar document from the corpus.
        """
        raise NotImplementedError("Subclasses should implement this method.")

    def most_similar_section(
        self, title: str, sections: list[Section]
    ) -> Section | None:
        """
        Find the most similar section in the sections according to the title.

        Args:
            title (str): The query string.
            sections (list[Section]): The list of sections to search.

        Returns:
            str | None: The most similar section or None if no similar title is found.
        """
        raise NotImplementedError("Subclasses should implement this method.")
