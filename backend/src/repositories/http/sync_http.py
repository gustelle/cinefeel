from contextlib import contextmanager
from typing import Generator, Literal

import hishel
import httpx
from loguru import logger

from src.exceptions import HttpError
from src.interfaces.http_client import IHttpClient
from src.settings import ScrapingSettings


class SyncHttpClient(IHttpClient):
    """executes HTTP requests synchronously

    The client cannot be serialized, we cannot share it across tasks and store it as a class attribute,
        thus we create a new client for each request.
        As a consequence we manage the rate limiting at prefect level using concurrency limits.
    """

    settings: ScrapingSettings

    def __init__(
        self,
        settings: ScrapingSettings,
    ):
        self.settings = settings

    @contextmanager
    def client(self) -> Generator[httpx.Client, None, None]:
        try:

            pwd = self.settings.mediawiki_api_key

            _client = hishel.CacheClient(
                storage=hishel.FileStorage(
                    base_path=".crawler_cache",
                    ttl=self.settings.cache_expire_after,
                ),
                follow_redirects=True,
                headers={
                    "User-Agent": self.settings.mediawiki_user_agent,
                    "Authorization": f"Bearer {pwd}",
                },
                timeout=self.settings.request_timeout,
            )
            yield _client
        finally:
            if _client and not _client.is_closed:
                try:
                    _client.close()
                except Exception as e:
                    logger.error(f"Error closing HTTP client connection: {e}")

    def send(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        response_type: Literal["json", "text"] = "json",
    ) -> dict | str:
        """Sends a GET request to the specified URL."""

        try:

            with self.client() as _client:

                response = _client.get(url, params=params, headers=headers)

                response.raise_for_status()

                return response.text if response_type == "text" else response.json()

        except httpx.TimeoutException as t:
            raise HttpError(reason=f"Request timed out: {t}", status_code=504)

        except httpx.HTTPStatusError as e:

            if e.response.status_code >= 400:
                logger.error(
                    f"failed to fetch '{url}': {e.response.status_code} - {params}"
                )

            raise HttpError(
                reason=f"HTTP error occurred: {e.response.status_code} - {e.response.text}",
                status_code=e.response.status_code,
            )
