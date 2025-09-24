import numpy
import pytest

from src.entities.movie import FilmActor, Movie


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
    film = Movie(
        uid="film-1",
        title="Test Film",
        permalink="http://example.com/test-film",
        actors=numpy.ndarray([actor]),
    )

    # when
    film.model_dump_json()

    # then
    assert True  # no exception raised


def test_load_from_json():
    """
    Test that Film can be loaded from JSON.
    """

    # given
    json_data = {
        "woa_type": "movie",
        "uid": "abiribidisciplinairesfrancais",
        "title": "À Biribi, disciplinaires français",
        "permalink": "https://fr.wikipedia.org/wiki/%C3%80_Biribi%2C_disciplinaires_fran%C3%A7ais",
        "summary": {
            "uid": "abiribidisciplinairesfrancais_filmsummary",
            "parent_uid": "abiribidisciplinairesfrancais",
            "score": 0.0,
            "content": "Un militaire et son supérieur sont épris de la même dame. Emporté par la jalousie, le militaire s'en prend au supérieur qui, en représailles, le fait incarcérer. Le verdict du tribunal militaire est sans appel: il est condamné à être déporté dans un établissement pénitentiaire militaire. Là-bas, des prisonniers sont soumis à des châtiments et des pratiques inhumaines pour toute désobéissance. Pris dans les mailles d'une machination ourdie en prison, le militaire se retrouve enfermé dans un silo, situation dont il n'aurait pas réchappé sans l'intervention d'un compagnon. Les deux hommes concoctent un plan d'évasion qui, tragiquement, se solde par leur décès.",
        },
        "specifications": {
            "uid": "abiribidisciplinairesfrancais_filmspecifications",
            "parent_uid": "abiribidisciplinairesfrancais",
            "score": 0.0,
            "title": "À Biribi, disciplinaires français",
            "release_date": "26 avril 1907",
            "directed_by": ["Lucien Nonguet"],
            "duration": "00:08:20",
        },
    }

    # when
    film = Movie.model_validate(json_data, by_name=True)

    # then
    assert film.uid == json_data["uid"]
    assert film.title == json_data["title"]
    assert str(film.permalink) == json_data["permalink"]
    assert film.summary is not None
    assert film.summary.content == json_data["summary"]["content"]
    assert film.specifications is not None
    assert film.specifications.title == json_data["specifications"]["title"]
    assert (
        film.specifications.release_date == json_data["specifications"]["release_date"]
    )
    assert film.specifications.directed_by == json_data["specifications"]["directed_by"]
    assert film.specifications.duration == json_data["specifications"]["duration"]
