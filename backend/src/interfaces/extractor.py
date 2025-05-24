from typing import Protocol, Type

from src.entities.content import InfoBoxElement, WikiPageLink


class IHtmlExtractor(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def retrieve_inner_links(
        self, html_content: str, entity_type: Type, *args, **kwargs
    ) -> list[WikiPageLink]:
        """
        Parses the given HTML content and returns a list of `~T` objects.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            list[WikiPageLink]: A list of `WikiPageLink` objects representing the extracted links.
        """
        pass

    def retrieve_infoboxes(self, *args, **kwargs) -> list[InfoBoxElement] | None:
        """
        Retrieves the infobox elements from the sections.
        """
        raise NotImplementedError("Subclasses must implement this method.")
