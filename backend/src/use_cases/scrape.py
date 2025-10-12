from pathlib import Path

from prefect import deploy, flow

from src.entities.movie import Movie
from src.entities.person import Person
from src.settings import Settings

from .uc_types import EntityType


class ScrapingUseCase:
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
                    entrypoint="scraping.py:scraping_flow",
                ).to_deployment(
                    name="wikipedia_scraping_movies",
                    description="Scrapes movies from Wikipedia pages.",
                    parameters={
                        "settings": self.settings,
                        "pages": [
                            p
                            for p in self.settings.scraping_start_pages
                            if p.entity_type == Movie.__name__
                        ],
                    },
                    concurrency_limit=self.settings.prefect_flows_concurrency_limit,  # 2 deploys at a time
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
                            for p in self.settings.scraping_start_pages
                            if p.entity_type == Person.__name__
                        ],
                    },
                    concurrency_limit=self.settings.prefect_flows_concurrency_limit,  # 2 deploys at a time
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
