from src.entities.film import Film
from src.interfaces.entity_transformer import IEntityTransformer


class StubEntityTransformer(IEntityTransformer):
    """
    A stub implementation of the IContentParser interface for testing purposes.
    """

    is_parsed: bool = False

    def to_entity(self, title: str) -> dict:
        """
        Parse the given content and return a dictionary representation.

        Args:
            content (str): The content to parse.

        Returns:
            dict: A dictionary representation of the parsed content.
        """
        return Film(
            title=title,
        )
