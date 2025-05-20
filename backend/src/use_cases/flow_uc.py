import time

from loguru import logger

from src.repositories.flow_analyzer import analyze_films
from src.repositories.flow_downloader import download_film_pages
from src.repositories.flow_indexer import index_films
from src.settings import Settings


class WikipediaFilmAnalysisUseCase:
    """
    TODO: filter the settings on the list of films to start the analysis

    we should have 2 use cases:
    - one for analyzing the films
    - one for analyzing the persons
    """

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self):

        start_time = time.time()

        await download_film_pages(
            settings=self.settings,
        )

        analyze_films(
            settings=self.settings,
        )

        index_films(
            settings=self.settings,
        )

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
