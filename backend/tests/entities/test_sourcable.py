from string import ascii_letters, digits, punctuation, whitespace

import pytest
from pydantic import Field

from src.entities.source import SourcedContentBase, Storable


def test_uid_validation():
    # given
    quotes = "\"'"
    accents = "àâçéèêëîïôùûüÿ"

    valid_part = "0-A-toi_aussi"

    allowed_punctuation = {"_", "-"}
    forbidden_punctuation = "".join(list(set(punctuation) - allowed_punctuation))

    invalid_chain = (
        ascii_letters
        + digits
        + forbidden_punctuation
        + whitespace
        + quotes
        + accents
        + "0-a-toi_aussi"
    )

    # When
    storable = Storable(uid=invalid_chain)

    # Then
    assert storable.uid is not None and len(storable.uid) > 0
    assert valid_part.lower() in storable.uid.lower()
    assert not any(
        char in storable.uid
        for char in forbidden_punctuation + whitespace + quotes + accents
    )


def test_permalink_is_mandatory():
    # given
    uid = "uid-12345"

    # when
    with pytest.raises(ValueError) as exc_info:
        SourcedContentBase(uid=uid, title="test", permalink=None)

    # then
    assert "permalink" in str(exc_info.value)


def test_serialize_by_alias_is_default_behavior():

    # given
    uid = "uid-12345"

    class MyStorable(Storable):
        my_field: str = Field(
            ...,
            serialization_alias="coucou",
        )

    my_instance = MyStorable(uid=uid, my_field="Hello World")

    # when
    serialized = my_instance.model_dump_json()

    # then
    assert serialized == '{"uid":"uid-12345","coucou":"Hello World"}'


def test_load_model_from_json_with_alias():

    # given

    class MyStorable(Storable):
        my_field: str = Field(
            ...,
            serialization_alias="coucou",
            validation_alias="coucou",
        )

    serialized = '{"uid":"uid-12345","coucou":"Hello World"}'

    # when
    instance = MyStorable.model_validate_json(serialized)

    # then
    assert instance.my_field == "Hello World"
