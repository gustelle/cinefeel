from src.interfaces.similarity import ISimilaritySearch


class StubSimilaritySearch(ISimilaritySearch):
    """
    A stub implementation of the ISimilaritySearch interface for testing purposes.
    """

    def most_similar(self, query: str, corpus: list[str]) -> str | None:
        """
        Return the first item in the corpus as the most similar item.
        """
        if not corpus:
            return None
        return corpus[0]
