import numpy
import pytest

from src.entities.composable import Composable
from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.entities.ml import ExtractionResult
from src.entities.woa import WOAInfluence


def test_from_parts_list_of_different_entities():

    base_info = Composable(
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    parts = [
        ExtractionResult(
            entity=FilmSummary(content="A thrilling film.", parent_uid=base_info.uid),
            score=0.95,
        ),
        ExtractionResult(
            entity=FilmMedia(
                trailers=["http://example.com/trailer"], parent_uid=base_info.uid
            ),
            score=0.90,
        ),
        ExtractionResult(
            entity=FilmSpecifications(title="Test Film", parent_uid=base_info.uid),
            score=0.85,
        ),
        ExtractionResult(
            entity=FilmActor(full_name="Brad Pitt", parent_uid=base_info.uid),
            score=0.80,
        ),
        ExtractionResult(
            entity=FilmActor(full_name="Linda", parent_uid=base_info.uid), score=0.80
        ),  # different actor
    ]

    film = Film.from_parts(base_info, parts)

    assert film.title == "Test Film"
    assert str(film.permalink) == "http://example.com/test-film"
    assert film.summary.content == "A thrilling film."
    assert len(film.media.trailers) == 1
    assert len(film.actors) == 2
    assert film.actors[0].full_name == "Brad Pitt"
    assert film.actors[1].full_name == "Linda"


@pytest.mark.skip("later, not implemented yet")
def test_from_parts_list_of_sames_entities():
    """
    - when 2 parts relate to the same entity, the one with the highest score is kept.
    """

    base_info = Composable(
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    parts = [
        ExtractionResult(
            entity=FilmSummary(
                uid="1", content="A thrilling film.", parent_uid=base_info.uid
            ),
            score=0.95,
        ),
        ExtractionResult(
            entity=FilmMedia(
                uid="1",
                trailers=["http://example.com/trailer"],
                parent_uid=base_info.uid,
            ),
            score=0.90,
        ),
        ExtractionResult(
            entity=FilmSpecifications(
                uid="1", title="Test Film", parent_uid=base_info.uid
            ),
            score=0.85,
        ),
        ExtractionResult(
            entity=FilmActor(
                uid="1",
                full_name="Brad Pitt",
                roles=["role1"],
                parent_uid=base_info.uid,
            ),
            score=0.80,
        ),
        ExtractionResult(
            entity=FilmActor(
                uid="1",
                full_name="Brad Pitt",
                roles=["role1"],
                parent_uid=base_info.uid,
            ),  # same actor, same role, but lower score
            score=0.70,
        ),  # Same actor, lower score, should be ignored
    ]

    film = Film.from_parts(base_info, parts)

    assert film.title == "Test Film"
    assert str(film.permalink) == "http://example.com/test-film"
    assert film.summary.content == "A thrilling film."
    assert len(film.media.trailers) == 1
    assert len(film.actors) == 1
    assert film.actors[0].full_name == "Brad Pitt"
    assert film.actors[0].roles == [
        "role1"
    ]  # Only the first role should be kept because it has a higher score


def test_from_parts_with_influences():
    """
    - when influences are present, they should be added to the film.
    """

    base_info = Composable(
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    woas = ["a nice painting that influenced the film"]

    parts = [
        ExtractionResult(
            entity=FilmSummary(
                uid="1", content="A thrilling film.", parent_uid=base_info.uid
            ),
            score=0.95,
        ),
        ExtractionResult(
            entity=WOAInfluence(
                uid="influence-1", work_of_arts=woas, parent_uid=base_info.uid
            ),
            score=0.75,
        ),
    ]

    film = Film.from_parts(base_info, parts)
    assert len(film.influences) == 1
    assert film.influences[0].work_of_arts == woas


@pytest.mark.skip
def test_serialize_roles_as_ndarray():
    """
    Test that roles in FilmActor are serialized as an array.
    """

    # given

    actor = FilmActor(
        uid="actor-1",
        full_name="John Doe",
        roles=numpy.ndarray(["Director", "Writer"]),
    )
    film = Film(
        uid="film-1",
        title="Test Film",
        permalink="http://example.com/test-film",
        actors=numpy.ndarray([actor]),
    )

    # when
    film.model_dump_json()

    # then
    assert True  # no exception raised
