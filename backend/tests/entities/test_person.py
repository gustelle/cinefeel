from jsonschema import validate

from src.entities.person import PersonCharacteristics


def test_serialization():

    # given
    characteristics = PersonCharacteristics(
        disabilities=["blind", "deaf"],
    )

    # when
    serialized = characteristics.model_dump_json(by_alias=True, exclude_none=True)

    # then
    assert serialized == '{"handicaps":["blind","deaf"]}'


def test_model_schema():

    # given
    schema = PersonCharacteristics.model_json_schema(by_alias=True)

    # when
    result = validate(
        {
            "handicaps": ["sourd"],
        },
        schema=schema,
    )

    # then
    assert (
        result is None
    )  # validate does not return anything, it raises an error if validation fails


def test_populate_by_alias():

    # given
    input = '{"handicaps":["sourd", "aveugle"]}'

    # when
    characs = PersonCharacteristics.model_validate_json(input, by_alias=True)

    # then
    assert characs.disabilities == ["sourd", "aveugle"]
