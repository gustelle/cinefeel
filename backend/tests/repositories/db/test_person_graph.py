import pytest

from src.entities.person import Biography, Person
from src.repositories.db.person_graph import PersonGraphHandler


@pytest.fixture(scope="function")
def test_film_handler(test_db_settings):
    yield PersonGraphHandler(None, test_db_settings)


def test_select_loads_person_by_name(test_film_handler: PersonGraphHandler):
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

    test_film_handler.insert_many([person])

    # when
    retrieved_person = test_film_handler.select(person.uid)

    print(retrieved_person)

    # then
    assert retrieved_person is not None
    assert retrieved_person.biography.full_name == bio.full_name
