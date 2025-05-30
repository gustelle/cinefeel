from typing import Protocol


class ContentAnalysisError(Exception):
    """
    Custom exception for content analysis errors.
    """

    pass


class IContentAnalyzer[T](Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def analyze(
        self,
        content_id: str,
        html_content: str,
        *args,
        **kwargs,
    ) -> T | None:
        """
        Parses the given HTML content and returns an entity from it, either a Film or a Person.

        Args:
            content_id (str): The unique identifier for the content being analyzed.
            html_content (str): The HTML content to parse.

        Returns:
            T | None: An instance of type T (Film or Person) containing the parsed data, or
                None if the parsing fails or the content is not relevant.

        Raises:
            ContentAnalysisError: If there is an error while parsing the HTML content.

        """
        pass
