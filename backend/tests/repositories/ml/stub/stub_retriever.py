from typing import Type

from pydantic import HttpUrl

from src.entities.content import PageLink, Section
from src.exceptions import RetrievalError
from src.interfaces.info_retriever import IContentParser


class NoPermakinRetriever(IContentParser):

    def retrieve_permalink(self, html_content, *args, **kwargs):
        raise RetrievalError("Failed to retrieve permalink", status_code=404)

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        """
        Returns a predefined title for testing.
        """
        return "Test Page Title"

    def retrieve_orphan_paragraphs(self, html_content, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_inner_links(
        self, html_content: str, entity_type: Type, *args, **kwargs
    ) -> list[PageLink]:
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_infobox(self, *args, **kwargs) -> Section | None:
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_media(self, html_content, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")


class NoTitleRetriever(IContentParser):

    def retrieve_permalink(self, html_content, *args, **kwargs):
        return HttpUrl("https://example.com/test-page")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        raise RetrievalError("Failed to retrieve title", status_code=404)

    def retrieve_orphan_paragraphs(self, html_content, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_inner_links(
        self, html_content: str, entity_type: Type, *args, **kwargs
    ) -> list[PageLink]:
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_infobox(self, *args, **kwargs) -> Section | None:
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_media(self, html_content, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")


class StubHtmlRetriever(IContentParser):

    infoxbox_elements: list[Section] | None = None
    orphan_paragraphs: Section | None = None

    def __init__(
        self,
        infoxbox_elements: list[Section] | None = None,
        orphan_paragraphs: Section | None = None,
    ):

        self.infoxbox_elements = infoxbox_elements
        self.orphan_paragraphs = orphan_paragraphs

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

    def retrieve_media(self, html_content, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method.")

    def retrieve_orphan_paragraphs(
        self, html_content, *args, **kwargs
    ) -> Section | None:
        return self.orphan_paragraphs
