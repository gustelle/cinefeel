from enum import StrEnum
from string import ascii_letters, digits, punctuation, whitespace

import pytest
from pydantic import Field, field_validator

from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.ml import ExtractionResult


def test_use_enum_values():
    # given
    class MyEnum(StrEnum):
        VALUE1 = "value1"
        VALUE2 = "value2"

    class MyComposable(Composable):
        my_enum: MyEnum

    # when
    instance = MyComposable(
        my_enum=MyEnum.VALUE1, title="Test Title", permalink="http://example.com/test"
    )

    # then
    assert (
        instance.my_enum == "value1"
    )  # should use the enum value, not the enum instance


def test_validate_assignment():
    # given
    class MyComposable(Composable):
        some_field: str

        @field_validator("some_field")
        def validate_some_field(cls, value: str) -> str:
            value = f"modified-{value}"
            return value

    # when
    instance = MyComposable(
        title="Test Title", permalink="http://example.com/test", some_field="test"
    )
    instance.some_field = "new value"

    # then
    assert instance.some_field == "modified-new value"


def test_uid_validation():
    # given
    quotes = "\"'"
    accents = "àâçéèêëîïôùûüÿ"

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
    storable = Composable(
        uid=invalid_chain, title="test", permalink="http://example.com/test"
    )

    # Then
    assert storable.uid is not None and len(storable.uid) > 0
    assert not any(
        char in storable.uid
        for char in forbidden_punctuation + whitespace + quotes + accents
    )


def test_permalink_is_mandatory():
    # given
    uid = "uid-12345"

    # when
    with pytest.raises(ValueError) as exc_info:
        Composable(uid=uid, title="test", permalink=None)

    # then
    assert "permalink" in str(exc_info.value)


def test_compose_only_parts_with_same_uid():
    # given
    class MyStorable(EntityComponent):
        some_field: str
        some_other_field: str | None = None

    class MyComposable(Composable):
        field1: MyStorable

    base_info = Composable(
        title="My Parent",
        permalink="http://example.com/mystorable_1",
    )
    parts = [
        ExtractionResult(
            entity=MyStorable(some_field="value1", parent_uid=base_info.uid),
            score=0.8,  # only this part should be used
        ),
        ExtractionResult(
            entity=MyStorable(
                some_field="value2", parent_uid="blah", some_other_field="value2"
            ),
            score=0.9,  # this part should be ignored because it has a different parent_uid, even if it has a higher score
        ),
    ]

    # when
    instance = MyComposable.compose(
        base_info.uid, base_info.title, base_info.permalink, parts=parts
    )

    # then
    assert instance.field1.some_field == "value1"  # only the first part is used
    assert instance.field1.some_other_field is None  # no other field provided


def test_compose_basic_case():

    # given
    class MyComponent(EntityComponent):
        some_value: str

    class MyOtherComponent(EntityComponent):
        another_value: int

    class MyComposable(Composable):
        field1: MyComponent
        field2: list[MyOtherComponent] | None = None

    base_info = Composable(
        title="My Parent",
        permalink="http://example.com/mystorable_1",
    )
    parts = [
        ExtractionResult(
            entity=MyComponent(some_value="value1", uid="1", parent_uid=base_info.uid),
            score=0.9,
        ),
        ExtractionResult(
            entity=MyOtherComponent(
                another_value=42, uid="2", parent_uid=base_info.uid
            ),
            score=0.8,
        ),
        ExtractionResult(
            entity=MyOtherComponent(
                another_value=78, uid="3", parent_uid=base_info.uid
            ),
            score=0.85,
        ),
    ]

    # when
    instance = MyComposable.compose(
        base_info.uid, base_info.title, base_info.permalink, parts=parts
    )

    # then
    assert len(instance.field2) == 2


def test_construct_takes_best_score():

    # given
    class MyStorable(EntityComponent):
        some_field: str

    class MyOtherStorable(EntityComponent):
        another_field: int

    class MyComposable(Composable):
        field1: MyStorable
        field2: list[MyOtherStorable] | None = None

    base_info = Composable(
        title="My Storable",
        permalink="http://example.com/mystorable_1",
    )

    parts = [
        ExtractionResult(
            entity=MyStorable(some_field="value1", uid="1", parent_uid=base_info.uid),
            score=0.9,
        ),
        ExtractionResult(
            entity=MyStorable(some_field="value2", uid="1", parent_uid=base_info.uid),
            score=0.10,
        ),  # lower score, should be ignored
    ]

    # when
    instance = MyComposable.compose(
        base_info.uid, base_info.title, base_info.permalink, parts=parts
    )

    # then
    assert instance.field1.some_field == "value1"  # best score wins
    assert instance.field2 is None  # No second part, so field2 should be None


def test_construct_fine_grained_assembly_in_case_of_single_entity():
    """
    - when 2 parts relate to the same entity but fields are different, we try to merge them.

    --> case where the composable entity is a single entity, not a list of entities.
    """

    class MyStorable(EntityComponent):
        some_field: str | None = None
        some_other_field: str | None = None

    class MyComposable(Composable):
        field1: MyStorable

    # same uid for both parts to simulate the same entity
    uid = "1"

    base_info = Composable(
        title="My Storable",
        permalink="http://example.com/mystorable_1",
    )

    parts = [
        ExtractionResult(
            entity=MyStorable(
                some_field="some_field_value", uid=uid, parent_uid=base_info.uid
            ),
            score=0.9,
        ),
        # this time, some_field is not provided, but some_other_field is
        ExtractionResult(
            entity=MyStorable(
                some_other_field="some_other_field_value",
                uid=uid,
                parent_uid=base_info.uid,
            ),
            score=0.10,
        ),
    ]

    # when
    instance = MyComposable.compose(
        base_info.uid, base_info.title, base_info.permalink, parts=parts
    )

    # then
    assert instance.field1.some_field == "some_field_value"
    assert instance.field1.some_other_field == "some_other_field_value"  # merged field


def test_construct_fine_grained_assembly_in_case_of_list():
    """
    - when 2 parts relate to the same entity but fields are different, we try to merge them.

    --> case where the composable entity is a list of entities.

    """

    class MyStorable(EntityComponent):
        some_field: str | None = None
        some_other_field: list[str] | None = None

    class MyComposable(Composable):
        field1: MyStorable

    base_info = Composable(
        title="My Storable",
        permalink="http://example.com/mystorable_1",
    )

    parts = [
        ExtractionResult(
            entity=MyStorable(some_field="some_field_value", parent_uid=base_info.uid),
            score=0.9,
        ),
        # this time, some_field is not provided, but some_other_field is
        ExtractionResult(
            entity=MyStorable(
                some_other_field=["some_other_value_1"],
                parent_uid=base_info.uid,
            ),
            score=0.10,
        ),
        ExtractionResult(
            entity=MyStorable(
                some_other_field=["some_other_value_2"],
                parent_uid=base_info.uid,
            ),
            score=0.10,
        ),
    ]

    # when
    instance = MyComposable.compose(
        base_info.uid, base_info.title, base_info.permalink, parts=parts
    )

    # then
    assert instance.field1.some_field == "some_field_value"
    assert sorted(instance.field1.some_other_field) == sorted(
        [
            "some_other_value_1",
            "some_other_value_2",
        ]
    )  # merged fields


def test_compose_parts_by_name():
    """
    - parts are loaded by name, not by alias

    """

    class MyStorable(EntityComponent):
        some_field: str

    class MyComposable(Composable):
        field1: MyStorable = Field(..., validation_alias="field1_alias")

    base_info = Composable(
        title="My Storable",
        permalink="http://example.com/mystorable_1",
    )

    parts = [
        ExtractionResult(
            entity=MyStorable(some_field="some_field_value", parent_uid=base_info.uid),
            score=0.9,
        ),
    ]

    # when
    instance = MyComposable.compose(
        base_info.uid, base_info.title, base_info.permalink, parts=parts
    )

    # then
    assert instance.field1 is not None
