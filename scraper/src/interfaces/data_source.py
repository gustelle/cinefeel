from typing import Protocol

from interfaces.http_client import IHttpClient


class IDataSource(Protocol):
    """
    Interface for a data source.
    """

    scraper: IHttpClient

    def __init__(self, scraper: IHttpClient):
        """
        Initialize the data source with a scraper.

        Args:
            scraper (IScraper): The scraper to use for data retrieval.
        """
        self.scraper = scraper

    def get_data(self, *args, **kwargs) -> dict:
        """
        Get data from the data source.

        Returns:
            dict: The data from the data source.
        """
        pass
