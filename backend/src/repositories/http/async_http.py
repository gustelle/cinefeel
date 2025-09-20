from typing import Literal

import hishel
import httpx
from loguru import logger

from src.interfaces.http_client import HttpError, IHttpClient
from src.settings import Settings


class AsyncHttpClient(IHttpClient):

    client: httpx.AsyncClient

    def __init__(
        self,
        settings: Settings,
    ):
        self.settings = settings
        limits = httpx.Limits(max_connections=settings.scraping_max_concurrency)

        self.client = hishel.AsyncCacheClient(
            storage=hishel.AsyncFileStorage(
                base_path=".crawler_cache",
                ttl=settings.scraping_cache_expire_after,
            ),
            limits=limits,
            follow_redirects=True,
            headers={
                "User-Agent": self.settings.mediawiki_user_agent,
                "Authorization": f"Bearer {self.settings.mediawiki_api_key}",
            },
        )

        logger.info(
            f"AsyncHttpClient initialized with {settings.scraping_max_concurrency} connections"
        )

    async def send(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        response_type: Literal["json", "text"] = "json",
    ) -> dict | str:
        """
        Send a GET request.

        Args:
            endpoint (str): The API endpoint to call.
            headers (dict): The headers to include in the request.
            params (dict): The parameters to include in the request.
            response_type (str): The type of response to expect ('json' or 'text').

        Returns:
            dict: The response data if as_json is True, otherwise the raw response text.
        """

        try:

            response = await self.client.get(url, params=params, headers=headers)

            response.raise_for_status()
            return response.text if response_type == "text" else response.json()

        except httpx.HTTPStatusError as e:

            raise HttpError(
                message=f"HTTP error occurred: {e.response.status_code} - {e.response.text}",
                status_code=e.response.status_code,
            )

    async def __aexit__(self, *args):
        """
        Close the client when exiting the context.
        """

        if not self.client.is_closed:
            logger.debug("Closing HTTP client connection.")
            await self.client.close()
