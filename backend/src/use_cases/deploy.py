from prefect import serve
from prefect.events import DeploymentEventTrigger

from src.repositories.task_orchestration.extraction_pipeline import (
    batch_extraction_flow,
)
from src.repositories.task_orchestration.relations_pipeline import (
    on_permalink_not_found,
    relationship_processor_flow,
)
from src.settings import Settings


class DeployFlowsUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        event_flow = on_permalink_not_found.to_deployment(
            name="On Permalink Not Found",
            triggers=[
                DeploymentEventTrigger(
                    enabled=True,
                    expect={"extract.entity"},
                    parameters={"permalink": "{{ event.resource.id }}"},
                )
            ],
        )

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

        extract_movies = batch_extraction_flow.to_deployment(
            name="Wikipedia Film Extraction",
            parameters={
                "settings": self.settings,
                "page_links": [
                    p
                    for p in self.settings.download_start_pages
                    if p.entity_type == "Movie"
                ],
            },
            cron="0 0 * * *",  # Every day at midnight
        )

        extract_persons = batch_extraction_flow.to_deployment(
            name="Wikipedia Person Extraction",
            parameters={
                "settings": self.settings,
                "page_links": [
                    p
                    for p in self.settings.download_start_pages
                    if p.entity_type == "Person"
                ],
            },
            cron="0 0 * * *",  # Every day at midnight
        )

        serve(film_enrich, person_enrich, event_flow, extract_movies, extract_persons)
