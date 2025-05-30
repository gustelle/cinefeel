from src.entities.film import Film
from src.interfaces.content_parser import IContentExtractor


class StubContentParser[T: Film](IContentExtractor[T]):
    """
    A stub implementation of the IContentParser interface for testing purposes.
    """

    is_parsed: bool = False

    def __init__(self, returned_entity: T = None):
        """
        Initialize the stub parser with an optional entity to return.

        Args:
            returned_entity (T, optional): An entity to return when resolve is called.
        """
        self.returned_entity = returned_entity

    def resolve(self, content: str) -> Film:
        """
        Parse the given content and return a dictionary representation.

        Args:
            content (str): The content to parse.

        Returns:
            dict: A dictionary representation of the parsed content.
        """
        self.is_parsed = True
        return self.returned_entity
