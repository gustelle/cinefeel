from src.interfaces.similarity import MLProcessor


class StubSimplifier(MLProcessor):
    """
    A stub implementation of the ISimilaritySearch interface for testing purposes.
    """

    is_called: bool = False

    def process(self, content: str):

        self.is_called = True
        return content
