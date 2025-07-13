import pytest

from src.interfaces.http_client import HttpError


def test_sync_get_as_json():

    # given
    from src.repositories.http.sync_http import SyncHttpClient
    from src.settings import Settings

    settings = Settings()
    http_client = SyncHttpClient(settings=settings)

    name = "Lucien Nonguet"

    url = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"
    response = http_client.send(url, response_type="json")

    assert isinstance(response, dict)


def test_sync_get_as_text():

    # given
    from src.repositories.http.sync_http import SyncHttpClient
    from src.settings import Settings

    settings = Settings()
    http_client = SyncHttpClient(settings=settings)

    name = "Lucien Nonguet"

    url = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"
    response = http_client.send(url, response_type="text")

    assert isinstance(response, str)
    assert len(response) > 0


def test_sync_get_404():

    # given
    from src.repositories.http.sync_http import SyncHttpClient
    from src.settings import Settings

    settings = Settings()
    http_client = SyncHttpClient(settings=settings)

    url = "https://fr.wikipedia.org/404"

    with pytest.raises(HttpError) as e:
        http_client.send(url)

    assert e.value.status_code == 404


def test_sync_get_multiple_requests():
    """
    the client remains open between requests
    """

    # given
    from src.repositories.http.sync_http import SyncHttpClient
    from src.settings import Settings

    settings = Settings()
    http_client = SyncHttpClient(settings=settings)

    name = "Lucien Nonguet"

    url = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"

    # when
    response1 = http_client.send(url, response_type="json")
    response2 = http_client.send(url, response_type="json")

    # then
    assert isinstance(response1, dict)
    assert isinstance(response2, dict)
    assert response1 == response2
    assert http_client.client.is_closed is False
