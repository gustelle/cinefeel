import time

from loguru import logger

from src.entities.person import Person
from src.repositories.flows.extraction_pipeline import ExtractionPipeline
from src.settings import Settings


class WikipediaPersonExtractionUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self):

        start_time = time.time()

        await ExtractionPipeline(
            settings=self.settings,
            entity_type=Person,
        ).execute_pipeline()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
