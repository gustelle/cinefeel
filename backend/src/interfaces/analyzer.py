from typing import Protocol, Sequence

from src.entities.content import Section
from src.entities.source import BaseInfo


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
        content_id: str,
        html_content: str,
        *args,
        **kwargs,
    ) -> tuple[BaseInfo, Sequence[Section]] | None:
        """
        Parses the given HTML content and extracts relevant data into a list of `Section` objects.

        Args:
            content_id (str): The unique identifier for the content being analyzed.
            html_content (str): The HTML content to parse.

        Returns:
            Sequence[Section] | None: A list of `Section` objects representing the relevant data,
            or None if the parsing fails or the content is not relevant.

        """
        pass
