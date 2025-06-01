from typing import Literal, Protocol

from pydantic import HttpUrl

from src.entities.content import PageLink, Section


class RetrievalError(Exception):
    pass


class IInfoRetriever(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def retrieve_orphans(
        self,
        html_content: str,
        position: Literal["start", "beetwen", "end"] = "start",
        sections_tag: str = "section",
        *args,
        **kwargs
    ) -> Section:
        """
        Orphan paraphraphs are paragraphs that are not attached to any section.
        They are usually found at the beginning or at end of the HTML content

        this method should extract such paragraphs from the HTML content and return them as a `Section` object.

        About the position:
        - "before": the orphan paragraph is before the first section.
        - "beetwen": the orphan paragraph is between sections.
        - "after": the orphan paragraph is after the last section.

        Args:
            html_content (str): The HTML content to parse.
            position (Literal["before", "beetwen", "after"]): The position of the orphan paragraph in the HTML content.
            sections_tag (str): The HTML tag that contains the sections. Defaults to "section".
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            str: The extracted permalink from the HTML content.

        Raises:
            RetrievalError: if the permalink cannot be found in the HTML content.
        """
        pass

    def retrieve_permalink(self, html_content: str, *args, **kwargs) -> HttpUrl:
        """
        Extracts the permalink from the given HTML content.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            str: The extracted permalink from the HTML content.

        Raises:
            RetrievalError: if the permalink cannot be found in the HTML content.
        """
        pass

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        """
        Extracts the title from the given HTML content.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            str: The extracted title from the HTML content.

        Raises:
            RetrievalError: if the title cannot be found in the HTML content.
        """
        pass

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


        Raises:
            RetrievalError: if inner links cannot be found in the HTML content.
        """
        pass

    def retrieve_infoboxes(self, *args, **kwargs) -> list[Section] | None:
        """
        Retrieves the infobox elements and returns them as a list of `Section` objects.
        """
        raise NotImplementedError("Subclasses must implement this method.")
