from src.entities.person import Person


def test_uid_is_customized():
    # given
    content_id = "test_person"
    content = {
        "full_name": "Test Person",
    }

    # when
    person = Person(
        full_name=content["full_name"],
        person_id=content_id,
    )

    # then
    assert content_id in person.uid
