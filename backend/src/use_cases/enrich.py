from src.repositories.task_orchestration.relations_pipeline import (
    relationship_processor_flow,
)
from src.settings import Settings


class EnrichmentUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        relationship_processor_flow.serve(
            name="Film Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Movie",
            },
        )

        relationship_processor_flow.serve(
            name="Person Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Person",
            },
        )
