import time

from loguru import logger

from src.entities.person import Person
from src.repositories.flows.html_pipeline import Html2EntitiesPipeline
from src.settings import Settings


class WikipediaPersonAnalysisUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self):

        start_time = time.time()

        await Html2EntitiesPipeline(
            settings=self.settings,
            entity_type=Person,
        ).execute_pipeline()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
