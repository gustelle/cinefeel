from src.entities.film import (
    FilmActor,
    FilmAssembler,
)
from src.entities.woa import WOAInfluence


def test_assemble_several_actors():
    # Given a film specifications and summary
    actors = [
        FilmActor(
            full_name="Influence One",
            roles=["Inspiration"],
        ),
        FilmActor(
            full_name="Influence Two",
            roles=["Adaptation"],
        ),
    ]
    title = "Epic Film"
    permalink = "https://example.com/epic-film"
    uid = "12345"

    # When assembling the film
    film = FilmAssembler().assemble(
        uid=uid,
        title=title,
        permalink=permalink,
        parts=[*actors],
    )

    # Then the film should be correctly assembled
    assert film is not None
    assert film.uid is not None and len(film.uid) > 0
    assert film.title == title
    assert str(film.permalink) == permalink
    assert len(film.actors) == 2
    assert all(isinstance(part, FilmActor) for part in film.actors)


def test_assemble_several_influences():
    # Given a film with several influences
    influences = [
        WOAInfluence(work_of_arts=["Influence One", "Influence Two"]),
        WOAInfluence(work_of_arts=["Influence Three"]),
    ]
    title = "Influential Film"
    permalink = "https://example.com/influential-film"
    uid = "67890"

    # When assembling the film
    film = FilmAssembler().assemble(
        uid=uid,
        title=title,
        permalink=permalink,
        parts=[*influences],
    )

    # Then the film should be correctly assembled
    assert film is not None
    assert film.uid is not None and len(film.uid) > 0
    assert film.title == title
    assert str(film.permalink) == permalink
    assert len(film.influences) == 2
    assert all(isinstance(part, WOAInfluence) for part in film.influences)
