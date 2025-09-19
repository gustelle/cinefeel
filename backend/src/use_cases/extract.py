from pathlib import Path

from prefect import deploy, flow

from src.settings import Settings

from .uc_types import EntityType


class EntityExtractionUseCase:
    """Handles the scraping of Wikipedia pages for specific entity types."""

    settings: Settings
    _types: list[EntityType]

    def __init__(self, settings: Settings, types: list[EntityType]):
        self.settings = settings
        self._types = types

    def execute(self):

        _flows = []
        if "movies" in self._types:

            _flows.append(
                flow.from_source(
                    source=Path(__file__).parent.parent
                    / "repositories/orchestration/flows",
                    entrypoint="entities_extraction.py:extract_entities_flow",
                ).to_deployment(
                    name="movies_extraction",
                    description="Extracts movies from HTML content.",
                    parameters={
                        "settings": self.settings,
                        "entity_type": "Movie",
                    },
                    cron="0 0 * * *",  # Every day at midnight
                    job_variables={
                        "working_dir": Path(__file__)
                        .parent.parent.parent.resolve()
                        .as_posix(),
                    },
                )
            )

        if "persons" in self._types:

            _flows.append(
                flow.from_source(
                    source=Path(__file__).parent.parent
                    / "repositories/orchestration/flows",
                    entrypoint="entities_extraction.py:extract_entities_flow",
                ).to_deployment(
                    name="persons_extraction",
                    description="Extracts persons from HTML content.",
                    parameters={
                        "settings": self.settings,
                        "entity_type": "Person",
                    },
                    cron="0 0 * * *",  # Every day at midnight
                    job_variables={
                        "working_dir": Path(__file__)
                        .parent.parent.parent.resolve()
                        .as_posix(),
                    },
                )
            )

        deploy(
            *_flows,
            work_pool_name="local-processes",
        )
