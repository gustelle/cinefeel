from src.interfaces.content_splitter import Section
from src.interfaces.similarity import MLProcessor


class Return1stSearch(MLProcessor):
    """
    A stub implementation of the ISimilaritySearch interface for testing purposes.
    """

    sections: list[Section]

    def __init__(self, sections: list[Section]):
        self.sections = sections

    def process(self, title, sections):
        return self.sections[0] if self.sections else None
