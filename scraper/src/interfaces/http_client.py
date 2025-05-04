from typing import Literal, Protocol


class ScrapingError(Exception):

    status_code: int

    def __init__(self, message: str, status_code: int = 500):
        """
        Custom exception for scraping errors.

        Args:
            message (str): The error message.
        """
        self.status_code = status_code
        super().__init__(message)


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
        Scrape the given URL and return the data as a dictionary.

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
