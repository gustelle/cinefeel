from enum import StrEnum
from pathlib import Path

from prefect import deploy, flow

from src.settings import Settings


class ScrapingType(StrEnum):
    movies = "movies"
    persons = "persons"


class ScrapingUseCase:
    """Handles the scraping of Wikipedia pages for specific entity types."""

    settings: Settings
    _types: list[ScrapingType]

    def __init__(self, settings: Settings, types: list[ScrapingType]):
        self.settings = settings
        self._types = types

    def execute(self):

        _flows = []
        if "movies" in self._types:

            _flows.append(
                flow.from_source(
                    source=Path(__file__).parent.parent
                    / "repositories/orchestration/flows",
                    entrypoint="scraping.py:scraping_flow",
                ).to_deployment(
                    name="wikipedia_scraping_movies",
                    description="Scrapes movies from Wikipedia pages.",
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
                    entrypoint="scraping.py:scraping_flow",
                ).to_deployment(
                    name="wikipedia_scraping_persons",
                    description="Scrapes persons from Wikipedia pages.",
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
