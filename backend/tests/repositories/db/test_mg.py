from src.repositories.db.mg_core import AbstractMemGraph
from src.settings import Settings


def test_setup(test_db_settings: Settings):

    # given

    test_film_handler = AbstractMemGraph(
        settings=test_db_settings,
    )

    # when
    is_setup = test_film_handler.setup()

    # then
    assert is_setup is True
