from prefect import serve
from prefect.events import DeploymentEventTrigger

from src.repositories.task_orchestration.extraction_pipeline import (
    batch_extraction_flow,
)
from src.repositories.task_orchestration.relations_pipeline import (
    on_permalink_not_found,
    relationship_flow,
)
from src.settings import Settings


class ServeUseCase:
    """use the `serve` function to run flows immediately without needing to deploy them first
    this is useful for development and testing purposes, because you don't need to run prefect server in the background
    and you can see the logs directly in the console,

    NB: this is not suitable for production as it doesn't provide the same level of reliability and scalability
    as deploying flows properly with Prefect's deployment system.
    """

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        unit_extract_flow = on_permalink_not_found.to_deployment(
            name="Unit Extraction Flow",
            triggers=[
                DeploymentEventTrigger(
                    enabled=True,
                    expect={"extract.entity"},
                    parameters={
                        "permalink": "{{ event.resource.id }}",
                        "entity_type": "{{ event.payload.entity_type }}",
                    },
                )
            ],
        )

        movie_enrich = relationship_flow.to_deployment(
            name="Movie Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Movie",
            },
        )

        person_enrich = relationship_flow.to_deployment(
            name="Person Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Person",
            },
        )

        extract_movies = batch_extraction_flow.to_deployment(
            name="Wikipedia Movie Extraction",
            parameters={
                "settings": self.settings,
                "pages": [
                    p
                    for p in self.settings.download_start_pages
                    if p.entity_type == "Movie"
                ],
            },
        )

        extract_persons = batch_extraction_flow.to_deployment(
            name="Wikipedia Person Extraction",
            parameters={
                "settings": self.settings,
                "pages": [
                    p
                    for p in self.settings.download_start_pages
                    if p.entity_type == "Person"
                ],
            },
        )

        serve(
            movie_enrich,
            person_enrich,
            unit_extract_flow,
            extract_movies,
            extract_persons,
        )
