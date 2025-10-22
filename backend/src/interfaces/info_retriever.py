from abc import ABC, abstractmethod
from typing import Iterable

from pydantic import HttpUrl

from src.entities.content import Media, PageLink, Section


class IContentParser(ABC):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    @abstractmethod
    def retrieve_orphan_paragraphs(self, html_content: str, *args, **kwargs) -> Section:
        """
        Orphan paraphraphs are paragraphs that are not attached to any section.
        They are usually found at the beginning or at end of the HTML content

        this method should extract such paragraphs from the HTML content and return them as a `Section` object.

        Args:
            html_content (str): The HTML content to parse.
            sections_tag (str): The HTML tag used to identify sections in the HTML content.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            str: The extracted permalink from the HTML content.

        Raises:
            RetrievalError: if the permalink cannot be found in the HTML content.
        """
        pass

    @abstractmethod
    def retrieve_permalink(self, html_content: str, *args, **kwargs) -> HttpUrl:
        """
        Extracts the permalink from the given HTML content.
        The permalink is a URL that points to the canonical location of the content.

        Example:
            In Wikipedia, the permalink is the URL that points to the specific version of a page.
            >> see https://en.wikipedia.org/wiki/Permalink

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

    @abstractmethod
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

    @abstractmethod
    def retrieve_inner_links(
        self, html_content: str, *args, **kwargs
    ) -> Iterable[PageLink]:
        """
        Parses the given HTML content and returns a collection of `~PageLink` objects.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            Iterable[PageLink]: A collection of `PageLink` objects representing the extracted links.

        Raises:
            RetrievalError: if inner links cannot be found in the HTML content.
        """
        pass

    @abstractmethod
    def retrieve_infobox(self, html_content: str, *args, **kwargs) -> Section | None:
        """
        Retrieves the infobox and transforms it into a `Section` object
        """
        raise NotImplementedError("Subclasses must implement this method.")

    @abstractmethod
    def retrieve_media(self, html_content: str, *args, **kwargs) -> Iterable[Media]:
        """
        Retrieves media links from the HTML content.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            Iterable[str]: A collection of media links extracted from the HTML content.

        Raises:
            RetrievalError: if media links cannot be found in the HTML content.
        """
        raise NotImplementedError("Subclasses must implement this method.")
