from pydantic import HttpUrl

from src.entities.content import PageLink, Section
from src.interfaces.info_retriever import IContentParser


class StubContentParser(IContentParser):

    _is_called: bool = False
    inner_links: list[PageLink] | None = None

    def __init__(self, inner_links: list[PageLink] | None = None):
        self.inner_links = inner_links

    def retrieve_orphan_paragraphs(self, html_content: str, *args, **kwargs) -> Section:
        return Section(
            title="Orphan Paragraphs", content=["This is an orphan paragraph."]
        )

    def retrieve_permalink(self, html_content: str, *args, **kwargs) -> HttpUrl:
        return HttpUrl("https://example.com/permalink")

    def retrieve_title(self, html_content: str, *args, **kwargs) -> str:
        return "Example Title"

    def retrieve_inner_links(
        self, html_content: str, *args, **kwargs
    ) -> list[PageLink]:
        self._is_called = True
        return self.inner_links
