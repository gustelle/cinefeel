from __future__ import annotations

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, computed_field

from src.entities.composable import Composable


class RelationshipType(StrEnum):
    """An enumeration of possible relationship types."""

    @classmethod
    def from_string(cls, value: str) -> Self:
        """Convert a string to a RelationshipType."""
        _child_classes = cls.__subclasses__()
        for child in _child_classes:
            for item in list(child):
                if item.value == value:
                    return child(item)
        raise ValueError(f"Unknown relationship type: {value}")


class PeopleRelationshipType(RelationshipType):

    # people
    DIRECTED_BY = "DIRECTED_BY"
    ACTED_IN = "ACTED_IN"
    WRITTEN_BY = "WRITTEN_BY"
    SCRIPTED_BY = "SCRIPTED_BY"
    COMPOSED_BY = "COMPOSED_BY"
    SPECIAL_EFFECTS_BY = "SPECIAL_EFFECTS_BY"
    SCENOGRAPHY_BY = "SCENOGRAPHY_BY"
    INFLUENCED_BY = "INFLUENCED_BY"


class WOARelationshipType(RelationshipType):

    # Works of Art
    INSPIRED_BY = "INSPIRED_BY"
    BASED_ON = "BASED_ON"
    ADAPTED_FROM = "ADAPTED_FROM"


class CompanyRelationshipType(RelationshipType):
    # Companies
    PRODUCED_BY = "PRODUCED_BY"
    DISTRIBUTED_BY = "DISTRIBUTED_BY"


class BaseRelationship(BaseModel):
    """
    A base class representing a relationship between two entities.
    """

    model_config = ConfigDict(use_enum_values=True)

    from_entity: Composable
    relation_type: RelationshipType
    to_entity: Composable | None = None
    to_title: str | None = None

    @computed_field
    @property
    def is_strong(self) -> bool:
        return self.to_entity is not None

    @computed_field
    @property
    def to_entity_type(self) -> str:
        if self.is_strong:
            return self.to_entity.__class__.__name__
        else:
            return "Unknown"

    @computed_field
    @property
    def from_entity_type(self) -> str:
        return self.from_entity.__class__.__name__


class StrongRelationship(BaseRelationship):
    """A strong relationship means we have full details of both entities."""

    to_entity: Composable
    to_title: None = None


class LooseRelationship(BaseRelationship):
    """
    Sometimes we want to represent a relationship without having the full entity details.
    This class allows us to do that by using just the title of the target entity.
    """

    to_entity: None = None
    to_title: str
