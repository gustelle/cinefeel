from src.interfaces.nlp_processor import Processor


class StubSimplifier(Processor):

    is_called: bool = False

    def process(self, content: str):

        self.is_called = True
        return content
