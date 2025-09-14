from enum import StrEnum

from prefect import serve

from src.repositories.task_orchestration.extraction_pipeline import (
    batch_extraction_flow,
)
from src.settings import Settings


class ExtractionType(StrEnum):
    movies = "movies"
    persons = "persons"


class ExtractUseCase:
    """for debugging purposes, to run the extraction flow directly without needing to deploy it first"""

    settings: Settings
    _types: list[ExtractionType]

    def __init__(self, settings: Settings, types: list[ExtractionType]):
        self.settings = settings
        self._types = types

    def execute(self):

        _flows = []
        if "movies" in self._types:

            _flows.append(
                batch_extraction_flow.to_deployment(
                    name="Wikipedia Film Extraction",
                    parameters={
                        "settings": self.settings,
                        "pages": [
                            p
                            for p in self.settings.download_start_pages
                            if p.entity_type == "Movie"
                        ],
                    },
                    cron="0 0 * * *",  # Every day at midnight
                )
            )

        if "persons" in self._types:

            _flows.append(
                batch_extraction_flow.to_deployment(
                    name="Wikipedia Person Extraction",
                    parameters={
                        "settings": self.settings,
                        "pages": [
                            p
                            for p in self.settings.download_start_pages
                            if p.entity_type == "Person"
                        ],
                    },
                    cron="0 0 * * *",  # Every day at midnight
                )
            )

        serve(
            *_flows,
        )
