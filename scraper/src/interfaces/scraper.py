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


class IScraper(Protocol):
    """
    Interface for a web scraper.
    """

    def scrape(
        self,
        url: str,
        *args,
        response_type: Literal["json", "text"] = "json",
        **kwargs,
    ) -> dict:
        """
        Scrape the given URL and return the data as a dictionary.

        Args:
            url (str): The URL to scrape.

        Returns:
            dict: The scraped data.
        """
        pass

    def close(self):
        """
        Close the data source.
        """
        pass
