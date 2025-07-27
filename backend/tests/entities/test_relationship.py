from src.entities.relationship import (
    PeopleRelationshipType,
    RelationshipType,
)


def test_RelationshipType_from_string():
    assert RelationshipType.from_string("ACTED_IN") == PeopleRelationshipType.ACTED_IN
