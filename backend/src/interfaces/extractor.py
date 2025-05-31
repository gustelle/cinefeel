from typing import Protocol

from pydantic import BaseModel


class IContentExtractor(Protocol):
    """
    Interface for entity resolver classes.
    """

    def extract_entity(
        self, content: str, entity_type: BaseModel, *args, **kwargs
    ) -> BaseModel:
        """
        Extract entity from the provided content.

        Args:
            content (str): The content from which to extract the entity.
            entity_type (BaseModel): The type of entity to extract, which should be a subclass of BaseModel.
            *args: Additional positional arguments for the extraction process.
            **kwargs: Additional keyword arguments for the extraction process.

        Returns:
            BaseModel: An instance of the entity type containing the extracted data.
        """
        raise NotImplementedError("Subclasses must implement this method.")
