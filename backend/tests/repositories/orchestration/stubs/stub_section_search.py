from src.entities.content import Section
from src.interfaces.nlp_processor import Processor


class StubSectionSearch(Processor[Section]):
    """
    Class to handle BERT similarity calculations.
    """

    return_value: Section | None
    is_called: bool = False

    def __init__(self, return_value: Section | None = None):

        self.return_value = return_value

    def process(self, title: str, sections: list[Section]) -> Section | None:
        """
        Find the most similar `Section` to the given title within the list of sections.

        Args:
            title (str): The title to find the most similar section for.
            sections (list[Section]): The list of sections to search within.

        Returns:
            str | None: The most similar section title, or None if no similar title is found.
        """

        self.is_called = True

        return self.return_value
