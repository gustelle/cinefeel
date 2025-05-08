from typing import Protocol


class ILinkExtractor(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def extract_links(self, html_content: str, *args, **kwargs) -> list[str]:
        """
        Parses the given HTML content and returns a list of `~T` objects.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            list[Any]: A list of objects objects containing the title and link to the film page.
        """
        pass
