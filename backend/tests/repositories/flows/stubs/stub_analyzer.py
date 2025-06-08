from typing import Sequence

from pydantic import HttpUrl

from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.interfaces.analyzer import IContentAnalyzer


class StubAnalyzer(IContentAnalyzer):

    is_analyzed: bool = False

    def process(
        self, *args, **kwargs
    ) -> tuple[SourcedContentBase, Sequence[Section]] | None:
        # This is a stub method that simulates analysis
        self.is_analyzed = True
        return (
            SourcedContentBase(
                uid="stub_film_id",
                title="Stub Film Title",
                permalink=HttpUrl("http://example.com/stub-film"),
            ),
            [
                Section(
                    title="Stub Section",
                    content="This is a stub section content.",
                )
            ],
        )
