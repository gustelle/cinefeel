from typing import Literal

import hishel
import httpx
from loguru import logger
from ratelimit import limits

from src.interfaces.http_client import HttpError, IHttpClient
from src.settings import Settings


class SyncHttpClient(IHttpClient):
    """executes HTTP requests synchronously
    this is useful for cases where you need to keep synchronous code for GPU processing
    or other synchronous libraries that do not support async/await
    """

    settings: Settings

    client: httpx.Client

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings
        limits = httpx.Limits(max_connections=settings.scraping_max_concurrency)

        pwd = self.settings.mediawiki_api_key

        self.client = hishel.CacheClient(
            storage=hishel.FileStorage(
                base_path=".crawler_cache",
                ttl=settings.scraping_cache_expire_after,
            ),
            limits=limits,
            follow_redirects=True,
            headers={
                "User-Agent": self.settings.mediawiki_user_agent,
                "Authorization": f"Bearer {pwd}",
            },
            timeout=settings.scraping_request_timeout,
        )

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Close the HTTP client when exiting the context.

        here we don't use a context manager because we want to keep the client open
        between requests. Using a context manager would close the client after the first request
        which would violate the principle of httpx.Client being reusable.
        """
        if not self.client.is_closed:
            logger.debug("Closing HTTP client connection.")
            self.client.close()

    # 4 requests per second
    @limits(calls=240, period=60)
    def send(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        response_type: Literal["json", "text"] = "json",
    ) -> dict | str:
        """Sends a GET request to the specified URL."""

        try:

            response = self.client.get(url, params=params, headers=headers)

            response.raise_for_status()

            return response.text if response_type == "text" else response.json()

        except httpx.TimeoutException as t:
            raise HttpError(message=f"Request timed out: {t}", status_code=504)

        except httpx.HTTPStatusError as e:

            if e.response.status_code >= 400:
                logger.error(
                    f"failed to fetch '{url}': {e.response.status_code} - {params}"
                )

            raise HttpError(
                message=f"HTTP error occurred: {e.response.status_code} - {e.response.text}",
                status_code=e.response.status_code,
            )
