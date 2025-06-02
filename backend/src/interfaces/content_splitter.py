from typing import Protocol

from src.entities.content import Section


class SplitterError(Exception):
    pass


class IContentSplitter(Protocol):
    """
    Interface for entity resolver classes.
    """

    def split(self, *args, **kwargs) -> list[Section] | None:
        """
        Splits the content into sections based on the specified tags.
        """
        raise NotImplementedError("Subclasses must implement this method.")
