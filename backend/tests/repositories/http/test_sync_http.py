import pytest
from pytest_httpx import HTTPXMock

from src.interfaces.http_client import HttpError


def test_sync_get_as_json(httpx_mock: HTTPXMock):

    # given
    from src.repositories.http.sync_http import SyncHttpClient
    from src.settings import Settings

    settings = Settings()
    http_client = SyncHttpClient(settings=settings)

    name = "Lucien Nonguet"

    url = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"

    httpx_mock.add_response(
        json={"title": name},
    )

    # when
    response = http_client.send(url, response_type="json")

    # then
    assert isinstance(response, dict)


def test_sync_get_as_text(httpx_mock: HTTPXMock):

    # given
    from src.repositories.http.sync_http import SyncHttpClient
    from src.settings import Settings

    settings = Settings()
    http_client = SyncHttpClient(settings=settings)

    name = "Lucien Nonguet"

    url = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"

    httpx_mock.add_response(
        text="<html><head><title>Lucien Nonguet</title></head><body>...</body></html>",
    )

    # when
    response = http_client.send(url, response_type="text")

    assert isinstance(response, str)
    assert len(response) > 0


def test_sync_get_404(httpx_mock: HTTPXMock):

    # given
    from src.repositories.http.sync_http import SyncHttpClient
    from src.settings import Settings

    settings = Settings()
    http_client = SyncHttpClient(settings=settings)

    url = "https://fr.wikipedia.org/404"

    httpx_mock.add_response(
        status_code=404,
    )

    with pytest.raises(HttpError) as e:
        http_client.send(url)

    assert e.value.status_code == 404


def test_sync_get_multiple_requests(httpx_mock: HTTPXMock):
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

    httpx_mock.add_response(json={"title": name}, is_reusable=True)

    # when
    response1 = http_client.send(url, response_type="json")
    response2 = http_client.send(url, response_type="json")

    # then
    assert isinstance(response1, dict)
    assert isinstance(response2, dict)
    assert response1 == response2
    assert http_client.client.is_closed is False
