from jsonschema import validate

from src.entities.person import Person, PersonCharacteristics


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


def test_person_serialization():
    """verify that alias is used for serialization"""

    # given
    characteristics = PersonCharacteristics(
        uid="123",
        disabilities=["blind", "deaf"],
    )

    # when
    serialized = characteristics.model_dump_json(exclude_none=True)

    # then
    assert serialized == '{"uid":"123","handicaps":["blind","deaf"]}'


def test_model_schema():

    # given
    schema = PersonCharacteristics.model_json_schema()

    # when
    result = validate(
        {
            "handicaps": ["sourd"],
            "uid": "123",
        },
        schema=schema,
    )

    # then
    assert (
        result is None
    )  # validate does not return anything, it raises an error if validation fails


def test_from_dump_by_alias():

    # given
    input = '{"handicaps":["sourd", "aveugle"], "uid":"123"}'

    # when
    characs = PersonCharacteristics.model_validate_json(input)

    # then
    assert characs.disabilities == ["sourd", "aveugle"]
