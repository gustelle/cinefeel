
from src.entities.person import Biography, Person
from src.repositories.db.person_graph import PersonGraphHandler


def test_select_person(test_person_handler: PersonGraphHandler):
    # given

    person = Person(
        title="Christopher Nolan",
        permalink="https://example.com/christopher-nolan",
    )
    bio = Biography(
        parent_uid=person.uid,
        full_name="Christopher Nolan",
    )
    person.biography = bio

    test_person_handler.insert_many([person])

    # when
    retrieved_person = test_person_handler.select(person.uid)

    # then
    assert retrieved_person is not None
    assert retrieved_person.biography.full_name == bio.full_name
