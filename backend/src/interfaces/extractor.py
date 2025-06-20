from typing import Protocol

from pydantic import BaseModel

from src.entities.extraction import ExtractionResult
from src.entities.source import SourcedContentBase


class IDataMiner(Protocol):
    """
    Interface for entity resolver classes.
    """

    def extract_entity(
        self,
        content: str,
        entity_type: BaseModel,
        base_info: SourcedContentBase,
        *args,
        **kwargs
    ) -> ExtractionResult:
        """
        Extract entity from the provided content.

        Args:
            content (str): The content from which to extract the entity.
            entity_type (BaseModel): The type of entity to extract, which should be a subclass of BaseModel.
            base_info (SourcedContentBase): Base information including title, permalink, and uid.
            *args: Additional positional arguments for the extraction process.
            **kwargs: Additional keyword arguments for the extraction process.

        Returns:
            BaseModel: An instance of the entity type containing the extracted data.
        """
        raise NotImplementedError("Subclasses must implement this method.")
