from typing import Protocol

from entities.woa import WorkOfArt


class IContentParser(Protocol):
    """
    Interface for entity resolver classes.
    """

    def to_entity(self, *args, **kwargs) -> WorkOfArt:
        """
        Resolves an entity to its canonical form.

        Args:
            entity (str): The entity to resolve.

        Returns:
            str: The resolved entity.
        """
        raise NotImplementedError("Subclasses must implement this method.")
