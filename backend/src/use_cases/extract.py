from pathlib import Path

from prefect import deploy, flow

from src.entities.movie import Movie
from src.entities.person import Person
from src.settings import AppSettings

from .uc_types import EntityType


class EntityExtractionUseCase:
    """Handles the scraping of Wikipedia pages for specific entity types."""

    _app_settings: AppSettings

    _types: list[EntityType]

    def __init__(
        self,
        app_settings: AppSettings,
        types: list[EntityType],
    ):
        self._app_settings = app_settings
        self._types = types

    def execute(self):

        _flows = []
        if "movies" in self._types:

            _flows.append(
                flow.from_source(
                    source=Path(__file__).parent.parent
                    / "repositories/orchestration/flows",
                    entrypoint="extract.py:extract_entities_flow",
                ).to_deployment(
                    name="movies_extraction",
                    description="Extracts movies from HTML content.",
                    parameters={
                        "app_settings": self._app_settings,
                        "entity_type": Movie.__name__,
                    },
                    job_variables={
                        "working_dir": Path(__file__)
                        .parent.parent.parent.resolve()
                        .as_posix(),
                    },
                    concurrency_limit=self._app_settings.prefect_settings.flows_concurrency_limit,
                )
            )

        if "persons" in self._types:

            _flows.append(
                flow.from_source(
                    source=Path(__file__).parent.parent
                    / "repositories/orchestration/flows",
                    entrypoint="extract.py:extract_entities_flow",
                ).to_deployment(
                    name="persons_extraction",
                    description="Extracts persons from HTML content.",
                    parameters={
                        "app_settings": self._app_settings,
                        "entity_type": Person.__name__,
                    },
                    job_variables={
                        "working_dir": Path(__file__)
                        .parent.parent.parent.resolve()
                        .as_posix(),
                    },
                    concurrency_limit=self._app_settings.prefect_settings.flows_concurrency_limit,
                )
            )

        deploy(
            *_flows,
            work_pool_name="local-processes",
        )
