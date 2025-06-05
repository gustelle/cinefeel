from src.entities.extraction import ExtractionResult
from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.entities.source import SourcedContentBase


def test_from_parts():

    base_info = SourcedContentBase(
        uid="film-123",
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    parts = [
        ExtractionResult(entity=FilmSummary(content="A thrilling film."), score=0.95),
        ExtractionResult(
            entity=FilmMedia(trailer="http://example.com/trailer"),
            score=0.90,
        ),
        ExtractionResult(
            entity=FilmSpecifications(title="Test Film"),
            score=0.85,
        ),
        ExtractionResult(entity=FilmActor(full_name="brad pitt"), score=0.80),
    ]

    film = Film.from_parts(base_info, parts, by_alias=True)

    print(film)

    assert film.uid == "film-123"
    assert film.title == "Test Film"
    assert str(film.permalink) == "http://example.com/test-film"
    assert film.summary.content == "A thrilling film."
    # assert film.media.media_type == "Trailer"
    # assert film.media.url == "http://example.com/trailer"
    # assert film.specifications.director == ["John Doe"]
    # assert film.specifications.duration == "01:30:00"
    # assert len(film.actors) == 1
    # assert film.actors[0].name == "Jane Smith"
    # assert film.actors[0].role == "Lead Actress"
