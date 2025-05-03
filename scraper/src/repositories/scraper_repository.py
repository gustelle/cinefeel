from typing import Literal

import aiohttp
from interfaces.scraper import IScraper, ScrapingError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    stop_after_delay,
)


class ConcurrentScraper(IScraper):
    """in charge of scraping data from the web using aiohttp"""

    _session: aiohttp.ClientSession

    def __init__(self, max_connections: int = 50):

        connector = aiohttp.TCPConnector(limit=max_connections)
        self._session = aiohttp.ClientSession(connector=connector)

        token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI2M2RjZGI2YmNiYTA2OTQ5NDFlMWJmM2FhZjk4OGU0MCIsImp0aSI6ImFiZDZlOTBlYzNhMzZkZDc3YjMwZGU0MDMyODAzZjUyNmIwY2Q4NjdmMmYzNDM0ODVjMTM2M2Q0YjRjY2ZmZmJjZjhhMWM5MmZiOTQyNDc0IiwiaWF0IjoxNzQ2Mjk3NjA5Ljg0NjQ2NSwibmJmIjoxNzQ2Mjk3NjA5Ljg0NjQ2NywiZXhwIjozMzMwMzIwNjQwOS44NDM0LCJzdWIiOiI3ODIzMzUwNyIsImlzcyI6Imh0dHBzOi8vbWV0YS53aWtpbWVkaWEub3JnIiwicmF0ZWxpbWl0Ijp7InJlcXVlc3RzX3Blcl91bml0Ijo1MDAwLCJ1bml0IjoiSE9VUiJ9LCJzY29wZXMiOlsiYmFzaWMiXX0.JNYW2SwVQbvBE6J07sR2x3JwTIZf2M7RVWbAZcczKXeReKy0EPyHMT2qGde82__oWt-3mQH71eDpi5XyyDY_ZxLlu2sm7xSHlXTcl2t7qFEKkakzp46cGNnk4EdwjzNVq-kcHsPiMcaUpz1K9gxIQISpdM0y9bwCbHmvWnrqth0OmeuISB1i1dVIYAc8Y13ipRLhlvWnVsn-tm6TqDwKPsE6FIvFSjgEZjxYm6dtLkmZwUwVziWdAPcV96CTyCSoormOoHKLXsrBbaqV9t1YOXwBGNKU1iR-SO4W1j-HaQ7pj9dpmSrSoRUitXJXqeh6tWb_uRz2ssGNfY_5nRjxiKW6tPWhCiLy_9VnbRYdyq8_stt2EEUZRwXJgbOfZIyFArw1c7LPtQ7GIlgXKiTYif06AmqNBREoyAJ4Q5YV09lLG_FwZ3wBWdcccJcnXY-R-9ibKzFQuQBhov0oUx-BH-u4Hl92KguxsqbQLjP2CGLt4VlzWmtNkQilE-SG-1Ez6OSy0uLeJAvShdcOxzZVPdWK5xNWfUpZLmDN8BLpp5aaqisWX8Ew9sa0OmTKRPi189azRjWpjza_rAOWHOkJnpfnWM1Xnb1yKwUSkGCBByAhVTl_OWU1L1E35i2falNYJ7z2h6M-g2VPUfs6FupdkVMPKNMxol59ExViswpSLlI"

        self._session.headers.update(
            {"User-Agent": "Cinefeel", "Authorization": f"Bearer {token}"}
        )

    @retry(
        retry=retry_if_exception_type(aiohttp.ClientError),
        stop=(stop_after_delay(180) | stop_after_attempt(3)),
        reraise=True,  # re-raise the last exception
    )
    async def scrape(
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
