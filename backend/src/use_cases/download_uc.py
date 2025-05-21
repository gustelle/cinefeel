import time

from loguru import logger

from src.repositories.flows.flow_chain import run_chain
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

        await run_chain(
            settings=self.settings,
        )

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
