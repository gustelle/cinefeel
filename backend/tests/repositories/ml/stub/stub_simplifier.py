from src.interfaces.nlp_processor import Processor


class StubSimplifier(Processor):
    """
    A stub implementation of the ISimilaritySearch interface for testing purposes.
    """

    is_called: bool = False

    def process(self, content: str):

        self.is_called = True
        return content
