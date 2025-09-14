from typing import Protocol, Sequence

from src.entities.composable import Composable
from src.entities.content import Section


class ContentAnalysisError(Exception):

    pass


class IContentAnalyzer(Protocol):
    """
    A content analyzer that extracts structured data from a given content.
    Contents may be HTML pages, text documents, etc.
    """

    def process(
        self,
        content_id: str,
        html_content: str,
        *args,
        **kwargs,
    ) -> tuple[Composable, Sequence[Section]] | None:
        """
        Extracts data from the provided content and returns a structured representation.

        Args:
            content_id (str): The unique identifier for the content being analyzed.
            html_content (str): The content to parse.

        Returns:
            Sequence[Section] | None: A list of `Section` objects representing the relevant data,
            or None if the parsing fails or the content is not relevant.

        """
        pass
