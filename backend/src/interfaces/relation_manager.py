from typing import Protocol, runtime_checkable

from src.entities.composable import Composable
from src.entities.relationship import Relationship


class RelationshipError(Exception):

    pass


@runtime_checkable
class IRelationshipHandler[U: Composable](Protocol):

    def add_relationship(
        self,
        relationship: Relationship,
        *args,
        **kwargs,
    ) -> None:
        """Adds a relationship between two contents.

        raises:
            RelationshipError: If the relationship cannot be added.
        """
        raise NotImplementedError("This method should be overridden by subclasses.")
