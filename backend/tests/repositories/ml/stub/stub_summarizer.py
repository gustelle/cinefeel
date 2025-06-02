from src.entities.content import Section
from src.interfaces.nlp_processor import MLProcessor


class StubSummarizer(MLProcessor):

    is_called: bool = False

    def process(self, section: Section) -> Section:

        self.is_called = True
        return section
