
from src.interfaces.http_client import IHttpClient


class StubHttpClient(IHttpClient):

    is_called = False
    raise_exc = Exception

    def __init__(
        self,
        response: dict | str,
        raise_exc: Exception = None,
    ):
        """
        Initializes the StubHttpClient with a predefined response.

        Args:
            response (dict | str): The response to return when send is called.
        """
        self._response = response
        self.raise_exc = raise_exc

    async def send(
        self,
        url: str,
        *args,
        **kwargs,
    ) -> dict | str:
        """
        Returns the predefined response without making an actual HTTP request.

        Args:
            url (str): The URL to scrape.
            response_type (str): The type of response expected ("json" or "text").

        Returns:
            dict | str: The predefined response.
        """
        self.is_called = True

        if self.raise_exc is not None:
            raise self.raise_exc

        return self._response

    def close(self):
        """
        Stub method to simulate closing the HTTP client.
        """
        pass
