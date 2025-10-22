from typing import Literal, Protocol



class IHttpClient(Protocol):
    """
    Interface for sending HTTP requests.
    """

    def send(
        self,
        url: str,
        *args,
        response_type: Literal["json", "text"] = "json",
        **kwargs,
    ) -> dict | str:
        """
        Calls the given URL and return the response.

        Args:
            url (str): The URL to scrape.

        Returns:
            dict: The scraped data as a dictionary if response_type is "json".
            str: The scraped data as a string if response_type is "text".
        """
        pass

    def close(self):
        """
        Close the data source.
        """
        pass
