from typing import Protocol, runtime_checkable

from src.entities.film import Film
from src.entities.person import Person


class RelationshipError(Exception):

    pass


@runtime_checkable
class IRelationshipHandler[U: Film | Person](Protocol):

    # the type of the entity being handled
    # e.g. Film or Person
    entity_type: U

    relation_type: U

    def add_relationship(
        self,
        content: U,
        relation_name: str,
        related_content: Film | Person,
        *args,
        **kwargs,
    ) -> U:
        """Adds a relationship between two contents."""
        raise NotImplementedError("This method should be overridden by subclasses.")
