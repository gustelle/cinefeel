import time

from loguru import logger

from src.interfaces.storage import IStorageHandler
from src.repositories.async_http import AsyncHttpClient
from src.repositories.dask_runner import DaskRunner
from src.repositories.wikipedia_crawler import WikipediaCrawler
from src.repositories.wikipedia_extractor import WikipediaLinkExtractor
from src.settings import Settings


class WikipediaCrawlUseCase:
    """TODO
    - test case where storage_handlers is void or None

    """

    storage_handlers: list[IStorageHandler]
    settings: Settings

    def __init__(
        self,
        storage_handlers: list[IStorageHandler] = None,
        settings: Settings = None,
    ):
        self.settings = settings or Settings()
        self.storage_handlers = storage_handlers

    async def execute(self):

        http_client = AsyncHttpClient(settings=self.settings)
        link_extractor = WikipediaLinkExtractor()
        task_runner = DaskRunner()

        # init the wikipedia repository here to run in the main thread
        # and avoid the "RuntimeError: Event loop is closed" error
        wiki_repo = WikipediaCrawler(
            http_client=http_client,
            link_extractor=link_extractor,
            settings=self.settings,
            task_runner=task_runner,
            storage_handlers=self.storage_handlers,
        )

        start_time = time.time()

        # get the films for each year
        async with task_runner:
            async with wiki_repo:
                await wiki_repo.crawl()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
