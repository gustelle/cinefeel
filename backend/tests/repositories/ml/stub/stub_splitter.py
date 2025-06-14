from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.interfaces.content_splitter import IContentSplitter
from src.interfaces.info_retriever import IInfoRetriever
from src.interfaces.nlp_processor import Processor


class StubHtmlSplitter(IContentSplitter):
    """
    A stub implementation of the IContentSplitter interface for testing purposes.
    """

    is_called = False

    def __init__(
        self, content_parser: IInfoRetriever = None, html_simplifier: Processor = None
    ):
        """
        Initializes the StubHtmlSplitter.
        This constructor does not require any parameters.
        """
        self.content_parser = content_parser
        self.html_simplifier = html_simplifier

    def split(self, *args, **kwargs) -> tuple[SourcedContentBase, list[Section]] | None:
        """
        Stub method to simulate splitting HTML content into sections.
        Returns an empty list to indicate no sections were found.
        """
        self.is_called = True
        return SourcedContentBase(
            uid="stub_uid", title="Stub Title", permalink="http://example.com/stub"
        ), [Section(title="Stub Section", content="This is a stub section content.")]
