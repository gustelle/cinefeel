import time

from loguru import logger

from src.entities.film import Film
from src.repositories.flows.entity_enrichment_pipeline import EntityEnrichmentProcessor
from src.settings import Settings


class EnrichmentUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        start_time = time.time()

        EntityEnrichmentProcessor(
            settings=self.settings,
            entity_type=Film,
        ).execute_pipeline()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
