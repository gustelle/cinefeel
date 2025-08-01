from prefect import deploy, flow
from prefect.events import DeploymentEventTrigger

from src.settings import Settings


class DeployFlowsUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        event_flow = flow.from_source(
            source="https://github.com/gustelle/cinefeel.git",
            entrypoint="src/repositories/task_orchestration/relations_pipeline.py:on_permalink_not_found",
        ).to_deployment(
            name="On Permalink Not Found",
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

        film_enrich = flow.from_source(
            source="https://github.com/gustelle/cinefeel.git",
            entrypoint="src/repositories/task_orchestration/relations_pipeline.py:relationship_flow",
        ).to_deployment(
            name="Film Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Movie",
            },
            cron="00 08 * * *",  # Every day at 8:00 AM
        )

        person_enrich = flow.from_source(
            source="https://github.com/gustelle/cinefeel.git",
            entrypoint="src/repositories/task_orchestration/relations_pipeline.py:relationship_flow",
        ).to_deployment(
            name="Person Enrichment",
            parameters={
                "settings": self.settings,
                "entity_type": "Person",
            },
            cron="00 09 * * *",  # Every day at 9:00 AM
        )

        extract_movies = flow.from_source(
            source="https://github.com/gustelle/cinefeel.git",
            entrypoint="src/repositories/task_orchestration/extraction_pipeline.py:batch_extraction_flow",
        ).to_deployment(
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

        extract_persons = flow.from_source(
            source="https://github.com/gustelle/cinefeel.git",
            entrypoint="src/repositories/task_orchestration/extraction_pipeline.py:batch_extraction_flow",
        ).to_deployment(
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

        deploy(film_enrich, person_enrich, event_flow, extract_movies, extract_persons)
