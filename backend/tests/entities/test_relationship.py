import pytest

from src.entities.person import Person
from src.entities.relationship import (
    LooseRelationship,
    PeopleRelationshipType,
    RelationshipType,
    StrongRelationship,
)


def test_RelationshipType_from_string():
    assert RelationshipType.from_string("ACTED_IN") == PeopleRelationshipType.ACTED_IN


def test_RelationshipType_from_string_invalid():
    with pytest.raises(ValueError):
        RelationshipType.from_string("INVALID_TYPE")


def test_StrongRelationship_props():
    # given
    person_a = Person(title="Some Actor", permalink="http://example.com/some-actor")
    person_b = person_a.model_copy(
        update={
            "title": "Some Director",
            "permalink": "http://example.com/some-director",
        }
    )

    # when
    relationship = StrongRelationship(
        from_entity=person_a,
        relation_type=PeopleRelationshipType.DIRECTED_BY,
        to_entity=person_b,
    )

    # then
    assert relationship.is_strong
    assert relationship.to_entity_type == "Person"
    assert relationship.from_entity_type == "Person"


def test_LooseRelationship_props():
    # given
    person = Person(title="Some Actor", permalink="http://example.com/some-actor")

    # when
    relationship = LooseRelationship(
        from_entity=person,
        relation_type=PeopleRelationshipType.ACTED_IN,
        to_title="Some Movie",
    )

    # then
    assert not relationship.is_strong
    assert relationship.to_entity_type == "Unknown"
    assert relationship.from_entity_type == "Person"
