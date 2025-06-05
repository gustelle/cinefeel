from src.entities.composable import Composable
from src.entities.extraction import ExtractionResult


def test_construct():

    # given
    class MyComposable(Composable):
        field1: str
        field2: list[int] | None = None

    parts = [
        ExtractionResult(entity="value1"),
        ExtractionResult(entity=[1, 2, 3]),
    ]

    # when
    instance = MyComposable.construct(parts=parts)

    # then
    assert instance.field1 == "value1"
    assert instance.field2 == [1, 2, 3]


def test_construct_takes_best_score():

    # given
    class MyComposable(Composable):
        field1: str
        field2: list[int] | None = None

    parts = [
        ExtractionResult(entity="value1", score=0.9),
        ExtractionResult(entity="value2", score=0.8),  # lower score, should be ignored
    ]

    # when
    instance = MyComposable.construct(parts=parts)

    # then
    assert instance.field1 == "value1"  # best score wins
    assert instance.field2 is None  # No second part, so field2 should be None
