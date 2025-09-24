from src.entities.composable import Composable
from src.entities.content import Section
from src.interfaces.content_splitter import IContentSplitter
from src.interfaces.info_retriever import IContentParser
from src.interfaces.nlp_processor import Processor


class StubHtmlSplitter(IContentSplitter):

    is_called = False

    def __init__(
        self, content_parser: IContentParser = None, html_simplifier: Processor = None
    ):
        """
        Initializes the StubHtmlSplitter.
        This constructor does not require any parameters.
        """
        self.content_parser = content_parser
        self.pruner = html_simplifier

    def split(self, *args, **kwargs) -> tuple[Composable, list[Section]] | None:
        """
        Stub method to simulate splitting HTML content into sections.
        Returns an empty list to indicate no sections were found.
        """
        self.is_called = True
        return Composable(
            uid="stub_uid", title="Stub Title", permalink="http://example.com/stub"
        ), [Section(title="Stub Section", content="This is a stub section content.")]
