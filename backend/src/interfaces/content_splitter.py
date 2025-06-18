from typing import Protocol

from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.interfaces.info_retriever import IParser
from src.interfaces.nlp_processor import Processor


class SplitterError(Exception):
    pass


class IContentSplitter(Protocol):
    """
    Interface for entity resolver classes.
    """

    info_retriever: IParser
    pruner: Processor

    def split(self, *args, **kwargs) -> tuple[SourcedContentBase, list[Section]] | None:
        """
        Splits the content into sections based on the specified tags.
        """
        raise NotImplementedError("Subclasses must implement this method.")
