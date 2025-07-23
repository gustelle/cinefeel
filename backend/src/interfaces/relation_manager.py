from enum import StrEnum
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from src.entities.composable import Composable


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


class WOARelationshipType(RelationshipType):

    # Works of Art
    INSPIRED_BY = "InspiredBy"
    BASED_ON = "BasedOn"
    ADAPTED_FROM = "AdaptedFrom"


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
