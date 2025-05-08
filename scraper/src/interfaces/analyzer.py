from typing import Protocol

from entities.film import Film
from entities.person import Person


class ContentAnalysisError(Exception):
    """
    Custom exception for content analysis errors.
    """

    pass


class IContentAnalyzer(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def analyze(
        self,
        html_content: str,
        *args,
        **kwargs,
    ) -> Film | Person | None:
        """
        Parses the given HTML content and returns an entity from it, either a Film or a Person.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            Film | Person | None: A Film or Person object containing the parsed data.
            None if the parsing fails or the content is not relevant.

        Raises:
            ContentAnalysisError: If there is an error while parsing the HTML content.

        """
        pass
