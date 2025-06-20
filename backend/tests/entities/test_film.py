from src.entities.extraction import ExtractionResult
from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.entities.source import SourcedContentBase


def test_from_parts_list_of_different_entities():

    base_info = SourcedContentBase(
        uid="film-123",
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    parts = [
        ExtractionResult(
            entity=FilmSummary(uid="1", content="A thrilling film."), score=0.95
        ),
        ExtractionResult(
            entity=FilmMedia(uid="1", trailers=["http://example.com/trailer"]),
            score=0.90,
        ),
        ExtractionResult(
            entity=FilmSpecifications(uid="1", title="Test Film"),
            score=0.85,
        ),
        ExtractionResult(entity=FilmActor(uid="1", full_name="Brad Pitt"), score=0.80),
        ExtractionResult(
            entity=FilmActor(uid="2", full_name="Linda"), score=0.80
        ),  # different actor
    ]

    film = Film.from_parts(base_info, parts)

    assert "film-123" in film.uid
    assert film.title == "Test Film"
    assert str(film.permalink) == "http://example.com/test-film"
    assert film.summary.content == "A thrilling film."
    assert len(film.media.trailers) == 1
    assert len(film.actors) == 2
    assert film.actors[0].full_name == "Brad Pitt"
    assert film.actors[1].full_name == "Linda"


def test_from_parts_list_of_sames_entities():
    """
    - when 2 parts relate to the same entity, the one with the highest score is kept.
    """

    base_info = SourcedContentBase(
        uid="film-123",
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    parts = [
        ExtractionResult(
            entity=FilmSummary(uid="1", content="A thrilling film."), score=0.95
        ),
        ExtractionResult(
            entity=FilmMedia(uid="1", trailers=["http://example.com/trailer"]),
            score=0.90,
        ),
        ExtractionResult(
            entity=FilmSpecifications(uid="1", title="Test Film"),
            score=0.85,
        ),
        ExtractionResult(
            entity=FilmActor(uid="1", full_name="Brad Pitt", roles=["role1"]),
            score=0.80,
        ),
        ExtractionResult(
            entity=FilmActor(
                uid="1", full_name="Brad Pitt", roles=["role1"]
            ),  # same actor, same role, but lower score
            score=0.70,
        ),  # Same actor, lower score, should be ignored
    ]

    film = Film.from_parts(base_info, parts)

    assert "film-123" in film.uid
    assert film.title == "Test Film"
    assert str(film.permalink) == "http://example.com/test-film"
    assert film.summary.content == "A thrilling film."
    assert len(film.media.trailers) == 1
    assert len(film.actors) == 1
    assert film.actors[0].full_name == "Brad Pitt"
    assert film.actors[0].roles == [
        "role1"
    ]  # Only the first role should be kept because it has a higher score
