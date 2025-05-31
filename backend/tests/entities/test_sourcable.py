from string import ascii_letters, digits, punctuation, whitespace

import pytest

from src.entities.source import Sourcable


def test_uid_validation():
    # given
    quotes = "\"'"
    accents = "àâçéèêëîïôùûüÿ"

    valid_part = "0-A-toi_aussi"

    allowed_punctuation = {"_", "-"}
    forbidden_punctuation = "".join(list(set(punctuation) - allowed_punctuation))

    invalid_chain = (
        ascii_letters
        + digits
        + forbidden_punctuation
        + whitespace
        + quotes
        + accents
        + "0-a-toi_aussi"
    )

    # When
    storable = Sourcable(uid=invalid_chain)

    # Then
    assert storable.uid is not None and len(storable.uid) > 0
    assert valid_part.lower() in storable.uid.lower()
    assert not any(
        char in storable.uid
        for char in forbidden_punctuation + whitespace + quotes + accents
    )


def test_permalink_is_mandatory():
    # given
    uid = "uid-12345"

    # when
    with pytest.raises(ValueError) as exc_info:
        Sourcable(uid=uid, permalink=None)

    # then
    assert "permalink" in str(exc_info.value)
