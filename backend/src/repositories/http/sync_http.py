from typing import Literal

import hishel
import httpx
from loguru import logger

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
        limits = httpx.Limits(
            max_connections=settings.scraper_max_concurrent_connections
        )

        pwd = self.settings.mediawiki_api_key

        self.client = hishel.CacheClient(
            storage=hishel.FileStorage(
                base_path=".crawler_cache",
                ttl=settings.crawler_cache_expire_after,
            ),
            limits=limits,
            follow_redirects=True,
            headers={
                "User-Agent": self.settings.scraper_user_agent,
                "Authorization": f"Bearer {pwd}",
            },
        )

        logger.info(
            f"SyncHttpClient initialized with {settings.scraper_max_concurrent_connections} connections ({pwd})"
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

    def send(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        response_type: Literal["json", "text"] = "json",
        timeout: int = 10,
    ) -> dict | str:
        """Sends a GET request to the specified URL."""

        try:

            response = self.client.get(
                url, params=params, headers=headers, timeout=timeout
            )

            response.raise_for_status()

            return response.text if response_type == "text" else response.json()

        except httpx.HTTPStatusError as e:

            raise HttpError(
                message=f"HTTP error occurred: {e.response.status_code} - {e.response.text}",
                status_code=e.response.status_code,
            )
