from src.entities.woa import WOAType, WorkOfArt


def test_uid_is_customized():
    # given
    content_id = "test_film"
    content = {
        "title": "Test Film",
        "release_date": "2023-01-01",
        "directors": ["John Doe"],
        "duration": 120,
        "genres": ["Drama"],
    }

    # when
    film = WorkOfArt(title=content["title"], woa_id=content_id, woa_type=WOAType.OPERA)

    # then
    assert film.uid.startswith(str(WOAType.OPERA))
    assert content_id in film.uid
