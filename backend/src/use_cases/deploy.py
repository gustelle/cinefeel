from pathlib import Path

from prefect import deploy, flow
from prefect.events import DeploymentEventTrigger

from src.settings import Settings


class DeployFlowsUseCase:

    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def execute(self):

        unit_extract_flow = flow.from_source(
            source=Path(__file__).parent.parent / "repositories/task_orchestration",
            entrypoint="relations_pipeline.py:on_permalink_not_found",
        ).to_deployment(
            name="unit_extraction_flow",
            description="Triggers when a permalink is not found in the storage which will trigger the extraction flow.",
            triggers=[
                DeploymentEventTrigger(
                    enabled=True,
                    expect={"extract.entity"},
                    parameters={
                        "permalink": "{{ event.resource.id }}",
                        "entity_type": "{{ event.payload.entity_type }}",
                        "settings": self.settings,
                    },
                )
            ],
            concurrency_limit=self.settings.prefect_concurrency_limit,
            job_variables={
                "working_dir": Path(__file__).parent.parent.parent.resolve().as_posix(),
            },
        )

        enrich_movies = flow.from_source(
            source=Path(__file__).parent.parent / "repositories/task_orchestration",
            entrypoint="relations_pipeline.py:relationship_flow",
        ).to_deployment(
            name="movies_enrichment",
            description="Adds relationships between movies and persons.",
            parameters={
                "settings": self.settings,
                "entity_type": "Movie",
            },
            cron="00 08 * * *",  # Every day at 8:00 AM
            job_variables={
                "working_dir": Path(__file__).parent.parent.parent.resolve().as_posix(),
            },
        )

        enrich_persons = flow.from_source(
            source=Path(__file__).parent.parent / "repositories/task_orchestration",
            entrypoint="relations_pipeline.py:relationship_flow",
        ).to_deployment(
            name="persons_enrichment",
            description="Adds relationships between persons and movies.",
            parameters={
                "settings": self.settings,
                "entity_type": "Person",
            },
            cron="00 09 * * *",  # Every day at 9:00 AM
            job_variables={
                "working_dir": Path(__file__).parent.parent.parent.resolve().as_posix(),
            },
        )

        extract_movies = flow.from_source(
            source=Path(__file__).parent.parent / "repositories/task_orchestration",
            entrypoint="extraction_pipeline.py:batch_extraction_flow",
        ).to_deployment(
            name="wikipedia_movies_extraction",
            description="Extracts films from Wikipedia pages.",
            parameters={
                "settings": self.settings,
                "pages": [
                    p
                    for p in self.settings.download_start_pages
                    if p.entity_type == "Movie"
                ],
            },
            cron="0 0 * * *",  # Every day at midnight
            job_variables={
                "working_dir": Path(__file__).parent.parent.parent.resolve().as_posix(),
            },
        )

        extract_persons = flow.from_source(
            source=Path(__file__).parent.parent / "repositories/task_orchestration",
            entrypoint="extraction_pipeline.py:batch_extraction_flow",
        ).to_deployment(
            name="wikipedia_persons_extraction",
            description="Extracts persons from Wikipedia pages.",
            parameters={
                "settings": self.settings,
                "pages": [
                    p
                    for p in self.settings.download_start_pages
                    if p.entity_type == "Person"
                ],
            },
            cron="0 0 * * *",  # Every day at midnight
            job_variables={
                "working_dir": Path(__file__).parent.parent.parent.resolve().as_posix(),
            },
        )

        deploy(
            enrich_movies,
            enrich_persons,
            unit_extract_flow,
            extract_movies,
            extract_persons,
            work_pool_name="local-processes",
        )
