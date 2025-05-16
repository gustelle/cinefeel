import asyncio

from loguru import logger

from src.interfaces.data_source import IDataSource
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.link_extractor import ILinkExtractor
from src.interfaces.storage import IStorageHandler
from src.interfaces.task_runner import ITaskRunner
from src.settings import Settings


class WikipediaCrawler(IDataSource):
    """
    this class is responsible for scraping Wikipedia pages and extracting film information.

    It must be used in a context manager to ensure that the scraper is closed properly.

    Example:
    ```python
        async with WikipediaRepository(...) as wiki_repo:
            films = await wiki_repo.crawl()
    ```
    """

    settings: Settings

    page_endpoint: str = "page/"
    links_extractor: ILinkExtractor
    async_task_runner: ITaskRunner
    storage_handler: IStorageHandler

    def __init__(
        self,
        http_client: IHttpClient,
        link_extractor: ILinkExtractor,
        settings: Settings,
        task_runner: ITaskRunner,
        storage_handler: IStorageHandler,
    ):
        super().__init__(scraper=http_client)
        self.links_extractor = link_extractor
        self.settings = settings
        self.async_task_runner = task_runner
        self.storage_handler = storage_handler

    async def download_page(
        self, page_id: str, storage_handler: IStorageHandler = None, **params
    ) -> str | None:
        """
        Get raw HTML from the Wikipedia API.

        Args:
            page_id (str): The ID of the page to retrieve.
            storage_handler (IStorageHandler, optional): The storage handler to use. Defaults to None.
                If not provided, no storage will be performed.
        """

        try:
            endpoint = (
                f"{self.settings.mediawiki_base_url}/{self.page_endpoint}{page_id}/html"
            )

            html = await self.scraper.send(
                endpoint=endpoint,
                response_type="text",
                params=params,
            )

            if html is not None and storage_handler is not None:
                self.storage_handler.insert(
                    content_id=page_id,
                    content=html,
                )

            return html

        except HttpError as e:
            if e.status_code == 404:
                logger.error(f"Page '{page_id}' not found")
            return None

    async def download(self, start_page: str) -> list[str]:
        """
        downloads the HTML pages and returns the list of page IDs.

        Args:
            start_page (str): The ID of the page containing the list of films.

        Returns:
            list[str]: A list of page IDs.
        """

        html = await self.download_page(page_id=start_page)

        if html is None:
            return []

        # extract the list of films from the HTML
        try:
            pages_ids: list[str] = await self.async_task_runner.submit(
                self.links_extractor.retrieve_inner_links,
                html_content=html,
                attrs={
                    "class": "wikitable",
                },
            )
        except Exception as e:
            logger.error(f"Error extracting list of films: {e}")
            return []

        # for each film, get the details
        details_tasks = [
            self.download_page(page_id=page_id, storage_handler=self.storage_handler)
            for page_id in pages_ids
        ]

        results = await asyncio.gather(*details_tasks)

        return results

    async def crawl(self) -> None:
        """
        Crawl the Wikipedia page and persist the data using the persistence handler.
        """

        tasks = []

        for page_id in self.settings.mediawiki_start_pages:
            tasks.append(
                self.download(
                    start_page=page_id,
                )
            )

        # wait for all tasks to complete
        # throttling is handled by the AsyncHttpClient
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error: {result}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.scraper.close()
