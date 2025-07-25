from typing import Protocol

from src.entities.composable import Composable
from src.entities.content import Section
from src.interfaces.info_retriever import IContentParser
from src.interfaces.nlp_processor import Processor


class SplitterError(Exception):
    pass


class IContentSplitter(Protocol):
    """
    Interface for entity resolver classes.
    """

    info_retriever: IContentParser
    pruner: Processor

    def split(self, *args, **kwargs) -> tuple[Composable, list[Section]] | None:
        """
        Splits the content into sections based on the specified tags.
        """
        raise NotImplementedError("Subclasses must implement this method.")
