from typing import Protocol

from src.entities.content import PageLink, Section


class IHtmlExtractor(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def retrieve_inner_links(
        self, html_content: str, *args, **kwargs
    ) -> list[PageLink]:
        """
        Parses the given HTML content and returns a list of `~T` objects.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            list[PageLink]: A list of `PageLink` objects representing the extracted links.
        """
        pass

    def retrieve_infoboxes(self, *args, **kwargs) -> list[Section] | None:
        """
        Retrieves the infobox elements and returns them as a list of `Section` objects.
        """
        raise NotImplementedError("Subclasses must implement this method.")
