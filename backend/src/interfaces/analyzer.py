from typing import Protocol, Sequence

from src.entities.composable import Composable
from src.entities.content import Section


class ContentAnalysisError(Exception):
    """
    Custom exception for content analysis errors.
    """

    pass


class IContentAnalyzer(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def process(
        self,
        content_id: str,
        html_content: str,
        *args,
        **kwargs,
    ) -> tuple[Composable, Sequence[Section]] | None:
        """
        Extracts data from the provided HTML content and returns a structured representation.

        Args:
            content_id (str): The unique identifier for the content being analyzed.
            html_content (str): The HTML content to parse.

        Returns:
            Sequence[Section] | None: A list of `Section` objects representing the relevant data,
            or None if the parsing fails or the content is not relevant.

        """
        pass
