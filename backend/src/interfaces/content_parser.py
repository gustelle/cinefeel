from typing import Protocol

from src.entities.film import Film
from src.entities.person import Person


class IContentParser[T: Film | Person](Protocol):
    """
    Interface for entity resolver classes.
    """

    def resolve(self, *args, **kwargs) -> T:
        """
        Resolves a content into an entity of type T, meaning that it extracts the relevant information
        from the content and returns an instance of the entity type T.

        Returns:
            T: An instance of the entity type T.
        """
        raise NotImplementedError("Subclasses must implement this method.")
