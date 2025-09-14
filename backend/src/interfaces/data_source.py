from typing import Generator, Protocol

from src.interfaces.http_client import IHttpClient


class ICrawler(Protocol):

    scraper: IHttpClient

    def __init__(self, scraper: IHttpClient):
        self.scraper = scraper

    def crawl(self, **kwargs) -> Generator[str, None, None]:
        """
        Crawl the data source and yields contents as strings.

        Args:
            **kwargs: Additional arguments to pass to the crawl method.

        Returns:
            Generator[str, None, None]: A generator of contents as strings.
        """
        pass
