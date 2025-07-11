import time

from loguru import logger

from src.entities.film import Film
from src.repositories.flows.entity_relationships_pipeline import (
    EntityRelationshipProcessor,
)
from src.settings import Settings


class RelationshipsUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        start_time = time.time()

        EntityRelationshipProcessor(
            settings=self.settings,
            entity_type=Film,
        ).execute_pipeline()

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
