from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from src.entities.composable import Composable
from src.entities.film import Film
from src.entities.person import Person


class RelationshipError(Exception):

    pass


class Relationship(BaseModel):
    """A class representing a relationship between two entities."""

    from_entity: Composable
    to_entity: Composable
    relation_type: str


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
    ) -> Relationship:
        """Adds a relationship between two contents."""
        raise NotImplementedError("This method should be overridden by subclasses.")
