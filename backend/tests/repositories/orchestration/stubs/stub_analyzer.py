from typing import Sequence

from pydantic import HttpUrl

from src.entities.composable import Composable
from src.entities.content import Section
from src.interfaces.analyzer import IContentAnalyzer


class StubAnalyzer(IContentAnalyzer):

    is_analyzed: bool = False

    def process(
        self,
        content_id: str,
        html_content: str,
        *args,
        **kwargs,
    ) -> tuple[Composable, Sequence[Section]] | None:
        # This is a stub method that simulates analysis
        self.is_analyzed = True
        return (
            Composable(
                title=f"Stub Film Title {content_id}",
                permalink=HttpUrl("http://example.com/stub-film"),
            ),
            [
                Section(
                    title=f"Stub Section {content_id}",
                    content=html_content[:50] + "...",
                )
            ],
        )
