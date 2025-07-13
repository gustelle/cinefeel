import asyncio
from typing import Literal

import aiohttp
from aiohttp_client_cache import CachedSession, FileBackend
from loguru import logger

from src.interfaces.http_client import HttpError, IHttpClient
from src.settings import Settings


class AsyncHttpClient(IHttpClient):
    """
    TODO:
    - migrate to httpx.AsyncClient to reduce dependencies
    """

    _session: aiohttp.ClientSession | CachedSession

    def __init__(
        self,
        settings: Settings,
    ):

        connector = aiohttp.TCPConnector(
            limit=settings.scraper_max_concurrent_connections,
            loop=asyncio.get_event_loop(),
        )

        if settings.crawler_use_cache:
            self._session = CachedSession(
                cache=FileBackend(
                    cache_name=".crawler_cache",
                    expire_after=settings.crawler_cache_expire_after,
                    cache_control=True,  # use cache-control headers if present
                ),
                connector=connector,
                loop=asyncio.get_event_loop(),
            )
        else:
            self._session = aiohttp.ClientSession(
                connector=connector,
                loop=asyncio.get_event_loop(),
            )

        self._session.headers.update(
            {
                "User-Agent": settings.scraper_user_agent,
                "Authorization": f"Bearer {settings.mediawiki_api_key}",
            }
        )

        logger.info(
            f"AsyncHttpClient initialized with {settings.scraper_max_concurrent_connections} connections"
        )

    async def send(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        response_type: Literal["json", "text"] = "json",
    ) -> dict:
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

        return await self._asend(
            url=url,
            headers=headers,
            params=params,
            response_type=response_type,
        )

    async def _asend(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        response_type: Literal["json", "text"] = "json",
    ) -> dict:
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

        # fix on booleans values for params:
        # see https://github.com/aio-libs/aiohttp/issues/4874
        params = {
            k: str(v).lower() if isinstance(v, bool) else v
            for k, v in (params or {}).items()
        }

        async with self._session.get(url, params=params, headers=headers) as response:

            try:

                response.raise_for_status()

                return (
                    await response.text()
                    if response_type == "text"
                    else await response.json()
                )

            except (aiohttp.ClientResponseError, aiohttp.ClientError) as e:

                raise HttpError(
                    f"Error {e.status} while fetching {url}: {e.message}",
                    status_code=e.status,
                ) from e

    async def close(self):
        """
        Close the aiohttp session.
        """
        await self._session.close()
        self._session = None
        # logger.info("Session closed")

    async def __aexit__(self, *args):
        """
        Close the aiohttp session when exiting the context manager.
        """
        await self.close()
