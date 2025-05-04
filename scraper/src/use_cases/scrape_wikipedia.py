import time

from entities.film import Film
from repositories.async_http import AsyncHttpClient
from repositories.dask_runner import DaskRunner
from repositories.wikipedia_crawler import WikipediaCrawler
from repositories.wikipedia_parser import WikipediaFilmParser
from settings import Settings


class WikipediaFilmScraperUseCase:

    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()

    async def execute(self) -> list[Film]:

        http_client = AsyncHttpClient(settings=self.settings)
        page_parser = WikipediaFilmParser()
        task_runner = DaskRunner()

        # init the wikipedia repository here to run in the main thread
        # and avoid the "RuntimeError: Event loop is closed" error
        wiki_repo = WikipediaCrawler(
            http_client=http_client,
            parser=page_parser,
            settings=self.settings,
            task_runner=task_runner,
        )

        start_time = time.time()

        films = []

        # get the films for each year
        async with task_runner:
            async with wiki_repo:
                films = await wiki_repo.crawl()

        end_time = time.time()
        print(f"Execution time: {end_time - start_time:.2f} seconds")

        return films
