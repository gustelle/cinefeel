import asyncio

from loguru import logger

from src.entities.film import Film
from src.entities.person import Person
from src.entities.wiki import WikiPageLink
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
    storage_handlers: list[IStorageHandler]

    def __init__(
        self,
        http_client: IHttpClient,
        link_extractor: ILinkExtractor,
        settings: Settings,
        task_runner: ITaskRunner,
        storage_handlers: list[IStorageHandler] = None,
    ):
        super().__init__(scraper=http_client)
        self.links_extractor = link_extractor
        self.settings = settings
        self.async_task_runner = task_runner
        self.storage_handlers = storage_handlers

    async def download_page(
        self, page_id: str, storage_handler: IStorageHandler = None, **params
    ) -> str | None:
        """
        Get raw HTML from the Wikipedia API.

        TODO:
        - testing of case where the page does not exist
        - testing of case storage_handler is None

        Args:
            page_id (str): The wikipedia ID of the page to download.
            storage_handler (IStorageHandler, optional): The storage handler to use. Defaults to None.
                If not provided, no storage will be performed.
        """

        try:

            logger.debug(
                f"Downloading page: {page_id} with storage handler: {storage_handler}"
            )

            endpoint = (
                f"{self.settings.mediawiki_base_url}/{self.page_endpoint}{page_id}/html"
            )

            html = await self.scraper.send(
                endpoint=endpoint,
                response_type="text",
                params=params,
            )

            if html is not None and storage_handler is not None:
                storage_handler.insert(
                    content_id=page_id,
                    content=html,
                )

            return html

        except HttpError as e:
            if e.status_code == 404:
                logger.error(f"Page '{page_id}' not found")
            return None

    async def download(self, start_page: str) -> list[WikiPageLink]:
        """
        downloads the HTML pages and returns the list of page IDs.

        TODO:
        - testing of case where an exception is raised in one of the tasks
        - case where person_storage_handler is None
        - case where film_storage_handler is None

        Args:
            start_page (str): The ID of the page containing the list of films.

        Returns:
            list[WikiPageLink]: A list of page links.
        """

        html = await self.download_page(page_id=start_page)

        if html is None:
            return []

        # extract the list of films from the HTML
        try:
            film_pages: list[WikiPageLink] = await self.async_task_runner.submit(
                self.links_extractor.retrieve_inner_links,
                html_content=html,
                css_selector=".wikitable td:nth-child(1)",  # first column of the table containing the films
            )

            person_pages: list[WikiPageLink] = await self.async_task_runner.submit(
                self.links_extractor.retrieve_inner_links,
                html_content=html,
                css_selector=".wikitable td:nth-child(2)",  # first column of the table containing the films
            )

        except Exception as e:
            logger.error(f"Error extracting list of films: {e}")
            return []

        # for each film, get the details
        film_details = [
            self.download_page(
                page_id=page.page_id,
                storage_handler=self._retrieve_storage_handler(Film),
            )
            for page in film_pages
        ]

        # for each person, get the details
        person_details = [
            self.download_page(
                page_id=page.page_id,
                storage_handler=self._retrieve_storage_handler(Person),
            )
            for page in person_pages
        ]

        all_pages = film_details + person_details

        results = await asyncio.gather(*all_pages, return_exceptions=True)

        return results

    async def crawl(self) -> None:
        """
        Crawl the Wikipedia page and persist the data using the persistence handler.

        TODO:
        - set a threshold for the number of pages to crawl
        - add a way to stop the crawling process
        - add a way to resume the crawling process
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

    def _retrieve_storage_handler(self, entity_type: type) -> IStorageHandler:
        """
        Get the storage handler for the given entity type.

        Args:
            entity_type (type): The type of the entity to get the storage handler for.

        Returns:
            IStorageHandler: The storage handler for the given entity type.
        """

        for handler in self.storage_handlers:
            if (
                isinstance(handler, IStorageHandler)
                and handler.entity_type is entity_type
            ):

                logger.debug(f"Storage handler: {handler}")
                return handler

        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.scraper.close()
