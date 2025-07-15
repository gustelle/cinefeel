from src.interfaces.relation_manager import PeopleRelationshipType
from src.repositories.flows.tasks.task_relationship import RelationshipData


def test_is_person_relationship():
    # given
    relationship = RelationshipData(
        related_entity_name="the_director",
        relation_type=PeopleRelationshipType.DIRECTED_BY,
    )

    # when
    is_person_relationship = relationship.is_person_relationship()

    # then
    assert is_person_relationship is True
