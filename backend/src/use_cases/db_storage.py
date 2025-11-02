from pathlib import Path

from prefect import deploy, flow

from src.entities.movie import Movie
from src.entities.person import Person
from src.settings import AppSettings

from .uc_types import EntityType


class DBStorageUseCase:
    """Handles the storage of entity data into the database."""

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
                    entrypoint="db_storage.py:db_storage_flow",
                ).to_deployment(
                    name="movies_storage",
                    description="Stores movies into the database.",
                    parameters={
                        "app_settings": self._app_settings,
                        "entity_type": Movie.__name__,
                    },
                    concurrency_limit=self._app_settings.prefect_settings.flows_concurrency_limit,
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
                    entrypoint="db_storage.py:db_storage_flow",
                ).to_deployment(
                    name="persons_storage",
                    description="Stores persons into the database.",
                    parameters={
                        "app_settings": self._app_settings,
                        "entity_type": Person.__name__,
                    },
                    concurrency_limit=self._app_settings.prefect_settings.flows_concurrency_limit,
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
