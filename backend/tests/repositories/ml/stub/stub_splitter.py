from src.entities.content import Section
from src.interfaces.content_splitter import IContentSplitter


class StubHtmlSplitter(IContentSplitter):
    """
    A stub implementation of the IContentSplitter interface for testing purposes.
    """

    is_called = False

    def split(self, *args, **kwargs) -> list[Section]:
        """
        Stub method to simulate splitting HTML content into sections.
        Returns an empty list to indicate no sections were found.
        """
        self.is_called = True
        return [
            Section(title="Stub Section", content="This is a stub section content.")
        ]
