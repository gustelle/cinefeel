from typing import Protocol

from interfaces.scraper import IScraper


class IDataSource(Protocol):
    """
    Interface for a data source.
    """

    scraper: IScraper

    def __init__(self, scraper: IScraper):
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
