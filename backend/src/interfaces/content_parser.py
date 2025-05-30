from typing import Protocol

from pydantic import BaseModel


class IContentExtractor(Protocol):
    """
    Interface for entity resolver classes.
    """

    def resolve(
        self, content: str, entity_type: BaseModel, *args, **kwargs
    ) -> BaseModel:
        """
        Resolves a content into an entity of type T, meaning that it extracts the relevant information
        from the content and returns an instance of the entity type T.

        Returns:
            T: An instance of the entity type T.
        """
        raise NotImplementedError("Subclasses must implement this method.")
