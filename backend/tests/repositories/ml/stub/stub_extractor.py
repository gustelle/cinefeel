from typing import Type

from src.entities.content import PageLink, Section
from src.interfaces.extractor import IHtmlExtractor


class StubHtmlExtractor(IHtmlExtractor):
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

    def retrieve_infoboxes(self, *args, **kwargs) -> list[Section] | None:
        """
        Returns a predefined list of InfoBoxElement objects for testing.
        """
        return self.infoxbox_elements if self.infoxbox_elements is not None else []
