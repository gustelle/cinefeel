import time

from interfaces.storage import IStorageHandler
from loguru import logger
from repositories.async_http import AsyncHttpClient
from repositories.dask_runner import DaskRunner
from repositories.wikipedia_crawler import WikipediaCrawler
from repositories.wikipedia_parser import WikipediaLinkExtractor
from settings import Settings


class WikipediaDownloadUseCase:

    storage_handler: IStorageHandler
    settings: Settings

    def __init__(self, storage_handler: IStorageHandler, settings: Settings = None):
        self.settings = settings or Settings()
        self.storage_handler = storage_handler

    async def execute(self):

        http_client = AsyncHttpClient(settings=self.settings)
        page_parser = WikipediaLinkExtractor()
        task_runner = DaskRunner()

        # init the wikipedia repository here to run in the main thread
        # and avoid the "RuntimeError: Event loop is closed" error
        wiki_repo = WikipediaCrawler(
            http_client=http_client,
            parser=page_parser,
            settings=self.settings,
            task_runner=task_runner,
            storage_handler=self.storage_handler,
        )

        start_time = time.time()

        # get the films for each year
        async with task_runner:
            async with wiki_repo:
                # TODO
                # manage start_urls and cut in chunks
                # to avoid too many requests
                await wiki_repo.crawl()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
