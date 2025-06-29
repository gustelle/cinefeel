from jsonschema import validate

from src.entities.extraction import ExtractionResult
from src.entities.person import Person, PersonCharacteristics, PersonVisibleFeatures


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
        },
        schema=schema,
    )

    # then
    assert (
        result is None
    )  # validate does not return anything, it raises an error if validation fails


def test_resolve_as():
    # given
    base_info = Person(
        uid="123",
        title="John Doe",
        permalink="http://example.com/john-doe",
    )
    parts = [
        ExtractionResult(
            score=0.9,
            entity=PersonVisibleFeatures(
                uid="123",
                skin_color="claire",
            ),
            resolve_as=PersonCharacteristics,
        )
    ]

    # when
    person = Person.from_parts(base_info, parts)

    # then
    assert (
        person.characteristics is not None
        and person.characteristics.skin_color == "claire"
    )
