import time

from loguru import logger

from src.entities.person import Person
from src.repositories.flows.pipeline import PipelineRunner
from src.settings import Settings


class WikipediaPersonAnalysisUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    async def execute(self):

        start_time = time.time()

        await PipelineRunner(
            settings=self.settings,
            entity_type=Person,
        ).run_chain()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
