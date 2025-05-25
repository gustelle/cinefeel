from src.entities.film import Film
from src.interfaces.content_parser import IContentParser


class StubContentParser[T: Film](IContentParser[T]):
    """
    A stub implementation of the IContentParser interface for testing purposes.
    """

    is_parsed: bool = False

    def resolve(self, content: str) -> Film:
        """
        Parse the given content and return a dictionary representation.

        Args:
            content (str): The content to parse.

        Returns:
            dict: A dictionary representation of the parsed content.
        """
        self.is_parsed = True
        return Film(
            title=content,
            uid="stub_film_id",
        )
