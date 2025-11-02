import pytest
from pytest_httpx import HTTPXMock

from src.exceptions import HttpError
from src.settings import AppSettings


def test_sync_get_as_json(httpx_mock: HTTPXMock, test_settings: AppSettings):

    # given
    from src.repositories.http.sync_http import SyncHttpClient

    settings = test_settings
    http_client = SyncHttpClient(settings=settings.scraping_settings)

    name = "Lucien Nonguet"

    url = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"

    httpx_mock.add_response(
        json={"title": name},
    )

    # when
    response = http_client.send(url, response_type="json")

    # then
    assert isinstance(response, dict)


def test_sync_get_as_text(httpx_mock: HTTPXMock, test_settings: AppSettings):

    # given
    from src.repositories.http.sync_http import SyncHttpClient

    settings = test_settings
    http_client = SyncHttpClient(settings=settings.scraping_settings)

    url = "https://fr.wikipedia.org/w/rest.php/v1/page/Lucien_Nonguet/bare"

    httpx_mock.add_response(
        text="<html><head><title>Lucien Nonguet</title></head><body>...</body></html>",
    )

    # when
    response = http_client.send(url, response_type="text")

    assert isinstance(response, str)
    assert len(response) > 0


def test_sync_get_404(httpx_mock: HTTPXMock, test_settings: AppSettings):

    # given
    from src.repositories.http.sync_http import SyncHttpClient

    settings = test_settings
    http_client = SyncHttpClient(settings=settings.scraping_settings)

    url = "https://fr.wikipedia.org/404"

    httpx_mock.add_response(
        status_code=404,
    )

    with pytest.raises(HttpError) as e:
        http_client.send(url)

    assert e.value.status_code == 404


def test_sync_get_multiple_requests(httpx_mock: HTTPXMock, test_settings: AppSettings):
    """
    the client remains open between requests
    """

    # given
    from src.repositories.http.sync_http import SyncHttpClient

    settings = test_settings
    http_client = SyncHttpClient(settings=settings.scraping_settings)

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


@pytest.mark.httpx_mock(assert_all_requests_were_expected=False)
def test_sync_timeout(httpx_mock: HTTPXMock, test_settings: AppSettings):

    # given
    from src.repositories.http.sync_http import SyncHttpClient

    settings = test_settings.scraping_settings
    settings.request_timeout = 1

    http_client = SyncHttpClient(settings=settings)

    url = "https://fr.wikipedia.org/w/rest.php/v1/page/Lucien_Nonguet/bare"

    httpx_mock.add_response(
        match_extensions={
            "timeout": {"connect": 10, "read": 10, "write": 10, "pool": 10}
        },
        is_optional=True,
    )

    with pytest.raises(HttpError) as e:
        http_client.send(url, response_type="text")

    assert e.value.status_code == 504
