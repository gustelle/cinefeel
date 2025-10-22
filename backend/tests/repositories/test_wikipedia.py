import pytest

from src.exceptions import RetrievalError
from src.repositories.wikipedia import get_page_id


def test_get_page_id():

    # given
    page_id = "Albert_Einstein"
    permalink = f"https://fr.wikipedia.org/wiki/{page_id}"

    # when
    _page_id = get_page_id(permalink)

    # then
    assert _page_id == page_id


def test_get_page_id_invalid_permalink():
    # given
    permalink = "https://fr.wikipedia.org/wrong_path/Albert_Einstein"

    # when / then
    with pytest.raises(Exception) as exc_info:
        v = get_page_id(permalink)
        print(v)

    assert isinstance(exc_info.value, RetrievalError)
    assert exc_info.value.status_code == 500
