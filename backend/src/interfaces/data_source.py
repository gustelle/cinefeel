from typing import Generator, Protocol

from src.interfaces.http_client import IHttpClient


class ICrawler(Protocol):
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

    def crawl(self, **kwargs) -> Generator[str, None, None]:
        """
        Crawl the data source and return a list of items.

        Args:
            **kwargs: Additional arguments to pass to the crawl method.

        Returns:
            list: A list of items retrieved from the data source.
        """
        pass
