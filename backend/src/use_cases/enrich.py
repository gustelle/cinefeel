from prefect import serve

from src.repositories.task_orchestration.relations_pipeline import (
    relationship_processor_flow,
)
from src.settings import Settings


class EnrichmentUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        film_enrich = relationship_processor_flow.to_deployment(
            name="Film Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Movie",
            },
            cron="00 08 * * *",  # Every day at 8:00 AM
        )

        person_enrich = relationship_processor_flow.to_deployment(
            name="Person Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Person",
            },
            cron="00 09 * * *",  # Every day at 9:00 AM
        )

        serve(
            film_enrich,
            person_enrich,
        )
