from src.interfaces.content_splitter import Section
from src.interfaces.similarity import ISimilaritySearch


class Return1stSearch(ISimilaritySearch):
    """
    A stub implementation of the ISimilaritySearch interface for testing purposes.
    """

    sections: list[Section]

    def __init__(self, sections: list[Section]):
        self.sections = sections

    def most_similar_section(self, title, sections):
        return self.sections[0] if self.sections else None
