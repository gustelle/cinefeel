from src.interfaces.nlp_processor import Processor


class DoNothingPruner(Processor[str]):

    is_called: bool = False

    def process(self, content: str) -> str:

        self.is_called = True
        return content
