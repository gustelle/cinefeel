from typing import Protocol

from src.entities.extraction import ExtractionResult
from src.entities.source import Storable


class IDataMiner(Protocol):
    """
    Interface for entity resolver classes.
    """

    def extract_entity(
        self, content: str, entity_type: Storable, *args, **kwargs
    ) -> ExtractionResult:
        """
        Extract entity from the provided content.

        Args:
            content (str): The content from which to extract the entity.
            entity_type (Storable): The type of entity to extract, which should be a subclass of `Storable`.
            *args: Additional positional arguments for the extraction process.
            **kwargs: Additional keyword arguments for the extraction process.

        Returns:
            ExtractionResult: The result of the extraction, containing the extracted entity and scoring (confidence) information.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def format(self, content: str) -> str:
        """
        Format the content before extraction.

        Args:
            content (str): The content to format.

        Returns:
            str: The formatted content.
        """
        raise NotImplementedError("Subclasses must implement this method.")
