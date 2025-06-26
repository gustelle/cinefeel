from src.interfaces.content_splitter import Section
from src.interfaces.nlp_processor import Processor


class StubSimilaritySearch(Processor):
    """
    A stub implementation of the ISimilaritySearch interface for testing purposes.
    """

    return_value: Section

    def __init__(self, return_value: Section):
        self.return_value = return_value

    def process(self, title, sections):
        return self.return_value


class ExactTitleSimilaritySearch(Processor):
    """
    A stub implementation of the ISimilaritySearch interface that returns a section
    with an exact title match.
    """

    def process(self, title, sections: list[Section]) -> Section | None:
        for section in sections:
            if section.title == title:
                return section
        return None
