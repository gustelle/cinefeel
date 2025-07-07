import numpy
import pytest

from src.entities.film import Film, FilmActor


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
