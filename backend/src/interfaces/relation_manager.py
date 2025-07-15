from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from src.entities.composable import Composable
from src.entities.film import Film
from src.entities.person import Person


class RelationshipError(Exception):

    pass


class RelationshipType(StrEnum):
    """An enumeration of possible relationship types."""

    pass


class PeopleRelationshipType(RelationshipType):
    """An enumeration of possible relationship types."""

    # people
    DIRECTED_BY = "DirectedBy"
    ACTED_IN = "ActedIn"
    WRITTEN_BY = "WrittenBy"
    SCRIPTED_BY = "ScriptedBy"
    COMPOSED_BY = "ComposedBy"
    SPECIAL_EFFECTS_BY = "SpecialEffectsBy"
    SCENOGRAPHY_BY = "ScenographyBy"
    INFLUENCED_BY = "InfluencedBy"


class CompanyRelationshipType(RelationshipType):
    # Companies
    PRODUCED_BY = "ProducedBy"
    DISTRIBUTED_BY = "DistributedBy"


class Relationship(BaseModel):
    """A class representing a relationship between two entities."""

    from_entity: Composable
    to_entity: Composable
    relation_type: RelationshipType


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
