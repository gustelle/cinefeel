from src.entities.film import Film
from src.entities.source import Sourcable
from src.interfaces.extractor import IContentExtractor


class StubExtractor(IContentExtractor):
    """
    A stub implementation of the IContentParser interface for testing purposes.
    """

    is_parsed: bool = False
    returned_entity: Sourcable

    def __init__(self, returned_entity: Sourcable):
        """
        Initialize the stub parser with an optional entity to return.

        Args:
            returned_entity (T, optional): An entity to return when resolve is called.
        """
        self.returned_entity = returned_entity

    def extract_entity(self, content: str) -> Film:
        """
        Parse the given content and return a dictionary representation.

        Args:
            content (str): The content to parse.

        Returns:
            dict: A dictionary representation of the parsed content.
        """
        self.is_parsed = True
        return self.returned_entity
