from typing import Type

from pydantic import HttpUrl

from src.entities.content import PageLink, Section
from src.interfaces.info_retriever import IInfoRetriever, RetrievalError


class NoPermakinRetriever(IInfoRetriever):
    """
    A stub implementation of the IHtmlExtractor interface that raises an error when trying to retrieve a permalink.
    This class is used to test error handling in the HTML extraction process.
    """

    def retrieve_permalink(self, html_content, *args, **kwargs):
        raise RetrievalError("Permalink retrieval is not supported in this stub.")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        """
        Returns a predefined title for testing.
        """
        return "Test Page Title"


class NoTitleRetriever(IInfoRetriever):
    """
    A stub implementation of the IHtmlExtractor interface that raises an error when trying to retrieve a title.
    This class is used to test error handling in the HTML extraction process.
    """

    def retrieve_permalink(self, html_content, *args, **kwargs):
        return HttpUrl("https://example.com/test-page")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        raise RetrievalError("Title retrieval is not supported in this stub.")


class StubHtmlRetriever(IInfoRetriever):
    """
    A stub implementation of the IHtmlExtractor interface for testing purposes.
    This class simulates the behavior of an HTML extractor without performing actual parsing.
    """

    infoxbox_elements: list[Section] | None = None

    def __init__(self, infoxbox_elements: list[Section] | None = None):
        """
        Initializes the StubHtmlExtractor.
        This constructor does not require any parameters.
        """
        self.infoxbox_elements = infoxbox_elements

    def retrieve_permalink(self, html_content, *args, **kwargs):
        return HttpUrl("https://example.com/test-page")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        """
        Returns a predefined title for testing.
        """
        return "Test Page Title"

    def retrieve_inner_links(
        self, html_content: str, entity_type: Type, *args, **kwargs
    ) -> list[PageLink]:
        """
        Returns a predefined list of WikiPageLink objects for testing.
        """
        return [
            PageLink(page_title="Test Page", page_id="Test_Page"),
            PageLink(page_title="Another Page", page_id="Another_Page"),
        ]

    def retrieve_infobox(self, *args, **kwargs) -> Section | None:
        """
        Returns a predefined list of InfoBoxElement objects for testing.
        """
        return self.infoxbox_elements[0] if self.infoxbox_elements is not None else None
