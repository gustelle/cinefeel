import asyncio
from typing import Literal

import aiohttp
from interfaces.http_client import IHttpClient, ScrapingError
from settings import Settings
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
)


class AsyncHttpClient(IHttpClient):
    """in charge of scraping data from the web using aiohttp"""

    _session: aiohttp.ClientSession

    def __init__(
        self,
        settings: Settings,
    ):

        connector = aiohttp.TCPConnector(
            limit=settings.scraper_max_concurrent_connections,
            loop=asyncio.get_event_loop(),
        )
        self._session = aiohttp.ClientSession(
            connector=connector, loop=asyncio.get_event_loop()
        )

        self._session.headers.update(
            {
                "User-Agent": settings.scraper_user_agent,
                "Authorization": f"Bearer {settings.mediawiki_api_key}",
            }
        )

        print(
            f"Scraper initialized with {settings.scraper_max_concurrent_connections} connections"
        )

    @retry(
        retry=retry_if_exception_type(aiohttp.ClientError),
        stop=(stop_after_delay(180) | stop_after_attempt(3)),
        reraise=True,  # re-raise the last exception
    )
    async def send(
        self,
        endpoint: str,
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

        async with self._session.get(
            endpoint, params=params, headers=headers
        ) as response:

            try:

                print(f"Requesting {endpoint}")

                response.raise_for_status()

                return (
                    await response.text()
                    if response_type == "text"
                    else await response.json()
                )

            except aiohttp.ClientResponseError as e:

                if response.status in [401, 403, 404, 429]:
                    print(
                        f"[{response.status}] Abandoning request to {endpoint} with params {params}"
                    )
                    raise ScrapingError(
                        f"Failed to fetch data from '{endpoint}': {e}",
                        status_code=response.status,
                    ) from e

                else:
                    # should be retried
                    raise

            except aiohttp.ContentTypeError as e:
                raise ScrapingError(
                    f"Failed to parse response from '{endpoint}': {e}",
                    status_code=e.status,
                ) from e

    async def close(self):
        """
        Close the aiohttp session.
        """
        await self._session.close()
        self._session = None
        print("Session closed")

    async def __aexit__(self, *args):
        """
        Close the aiohttp session when exiting the context manager.
        """
        await self.close()
