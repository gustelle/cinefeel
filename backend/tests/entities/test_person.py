from datetime import datetime

from jsonschema import validate

from src.entities.person import Biography, Person, PersonCharacteristics


def test_biography_may_be_None():
    # given
    bio = None

    # when
    person = Person(
        uid="123",
        title="John Doe",
        permalink="http://example.com/john-doe",
        biography=bio,
    )
    # then
    assert person.biography is None


def test_model_schema():

    # given
    schema = PersonCharacteristics.model_json_schema()

    # when
    result = validate(
        {
            "handicaps": ["auditif", "visuel"],
            "uid": "123",
            "parent_uid": "123",
        },
        schema=schema,
    )

    # then
    assert (
        result is None
    )  # validate does not return anything, it raises an error if validation fails


def test_load_bio_with_datetime():
    # given
    do_birth = datetime(1990, 1, 1)
    do_death = datetime(2020, 1, 1)

    # when
    bio = Biography(
        full_name="John Doe",
        parent_uid="123",
        birth_date=do_birth,
        death_date=do_death,
    )

    # then
    assert isinstance(bio.birth_date, str) and bio.birth_date == "1990-01-01"
    assert isinstance(bio.death_date, str) and bio.death_date == "2020-01-01"


def test_load_bio_with_none():
    # given
    do_birth = None
    do_death = None

    # when
    bio = Biography(
        full_name="John Doe",
        parent_uid="123",
        birth_date=do_birth,
        death_date=do_death,
    )

    # then
    assert bio.birth_date is None
    assert bio.death_date is None


def test_load_bio_with_string():

    # given
    do_birth = "1990-01-01"
    do_death = "2020-01-01"

    # when
    bio = Biography(
        full_name="John Doe",
        parent_uid="123",
        birth_date=do_birth,
        death_date=do_death,
    )

    # then
    assert isinstance(bio.birth_date, str) and bio.birth_date == "1990-01-01"
    assert isinstance(bio.death_date, str) and bio.death_date == "2020-01-01"
