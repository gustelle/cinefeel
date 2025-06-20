from src.entities.composable import Composable
from src.entities.extraction import ExtractionResult
from src.entities.source import Storable


def test_construct_basic_case():

    # given
    class MyStorable(Storable):
        some_field: str

    class MyOtherStorable(Storable):
        another_field: int

    class MyComposable(Composable):
        field1: MyStorable
        field2: list[MyOtherStorable] | None = None

    parts = [
        ExtractionResult(entity=MyStorable(some_field="value1", uid="1"), score=0.9),
        ExtractionResult(entity=MyOtherStorable(another_field=42, uid="2"), score=0.8),
        ExtractionResult(entity=MyOtherStorable(another_field=78, uid="3"), score=0.85),
    ]

    # when
    instance = MyComposable.construct(parts=parts)

    # then
    assert instance.field1.uid == "mystorable_1"
    assert len(instance.field2) == 2
    assert instance.field2[0].uid == "myotherstorable_2"
    assert instance.field2[1].uid == "myotherstorable_3"


def test_construct_takes_best_score():

    # given
    class MyStorable(Storable):
        some_field: str

    class MyOtherStorable(Storable):
        another_field: int

    class MyComposable(Composable):
        field1: MyStorable
        field2: list[MyOtherStorable] | None = None

    parts = [
        ExtractionResult(entity=MyStorable(some_field="value1", uid="1"), score=0.9),
        ExtractionResult(
            entity=MyStorable(some_field="value2", uid="1"), score=0.10
        ),  # lower score, should be ignored
    ]

    # when
    instance = MyComposable.construct(parts=parts)

    # then
    assert instance.field1.some_field == "value1"  # best score wins
    assert instance.field2 is None  # No second part, so field2 should be None


def test_construct_fine_grained_assembly_in_case_of_single_entity():
    """
    - when 2 parts relate to the same entity but fields are different, we try to merge them.

    --> case where the composable entity is a single entity, not a list of entities.
    """

    class MyStorable(Storable):
        some_field: str | None = None
        some_other_field: str | None = None

    class MyComposable(Composable):
        field1: MyStorable

    # same uid for both parts to simulate the same entity
    uid = "1"

    parts = [
        ExtractionResult(
            entity=MyStorable(some_field="some_field_value", uid=uid), score=0.9
        ),
        # this time, some_field is not provided, but some_other_field is
        ExtractionResult(
            entity=MyStorable(some_other_field="some_other_field_value", uid=uid),
            score=0.10,
        ),
    ]

    # when
    instance = MyComposable.construct(parts=parts)

    # then
    assert instance.field1.some_field == "some_field_value"
    assert instance.field1.some_other_field == "some_other_field_value"  # merged field


def test_construct_fine_grained_assembly_in_case_of_list():
    """
    - when 2 parts relate to the same entity but fields are different, we try to merge them.

    --> case where the composable entity is a list of entities.

    """

    class MyStorable(Storable):
        some_field: str | None = None
        some_other_field: list[str] | None = None

    class MyComposable(Composable):
        field1: MyStorable

    # all parts relate to the same entity, so we use the same uid
    uid = "1"

    parts = [
        ExtractionResult(
            entity=MyStorable(some_field="some_field_value", uid=uid), score=0.9
        ),
        # this time, some_field is not provided, but some_other_field is
        ExtractionResult(
            entity=MyStorable(some_other_field=["some_other_value_1"], uid=uid),
            score=0.10,
        ),
        ExtractionResult(
            entity=MyStorable(some_other_field=["some_other_value_2"], uid=uid),
            score=0.10,
        ),
    ]

    # when
    instance = MyComposable.construct(parts=parts)

    # then
    assert instance.field1.some_field == "some_field_value"
    assert sorted(instance.field1.some_other_field) == sorted(
        [
            "some_other_value_1",
            "some_other_value_2",
        ]
    )  # merged fields
