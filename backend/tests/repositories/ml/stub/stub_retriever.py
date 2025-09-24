from typing import Type

from pydantic import HttpUrl

from src.entities.content import PageLink, Section
from src.interfaces.info_retriever import IContentParser, RetrievalError


class NoPermakinRetriever(IContentParser):

    def retrieve_permalink(self, html_content, *args, **kwargs):
        raise RetrievalError("Failed to retrieve permalink")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        """
        Returns a predefined title for testing.
        """
        return "Test Page Title"


class NoTitleRetriever(IContentParser):

    def retrieve_permalink(self, html_content, *args, **kwargs):
        return HttpUrl("https://example.com/test-page")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        raise RetrievalError("Failed to retrieve title")


class StubHtmlRetriever(IContentParser):

    infoxbox_elements: list[Section] | None = None

    def __init__(self, infoxbox_elements: list[Section] | None = None):

        self.infoxbox_elements = infoxbox_elements

    def retrieve_permalink(self, html_content, *args, **kwargs):
        return HttpUrl("https://example.com/test-page")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:

        return "Test Page Title"

    def retrieve_inner_links(
        self, html_content: str, entity_type: Type, *args, **kwargs
    ) -> list[PageLink]:

        return [
            PageLink(page_title="Test Page", page_id="Test_Page"),
            PageLink(page_title="Another Page", page_id="Another_Page"),
        ]

    def retrieve_infobox(self, *args, **kwargs) -> Section | None:

        return self.infoxbox_elements[0] if self.infoxbox_elements is not None else None
