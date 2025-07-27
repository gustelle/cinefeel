import time

from loguru import logger

from src.entities.film import Film
from src.repositories.task_orchestration.extraction_pipeline import (
    BatchExtractionPipeline,
)
from src.settings import Settings


class WikipediaFilmExtractionUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self):

        start_time = time.time()

        await BatchExtractionPipeline(
            settings=self.settings,
            entity_type=Film,
        ).execute_pipeline()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
