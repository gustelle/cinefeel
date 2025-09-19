from pathlib import Path

from prefect import deploy, flow

from src.settings import Settings

from .uc_types import EntityType


class DBStorageUseCase:
    """Handles the storage of entity data into the database."""

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
                    entrypoint="db_storage.py:db_storage_flow",
                ).to_deployment(
                    name="movies_storage",
                    description="Stores movies into the database.",
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
                    entrypoint="db_storage.py:db_storage_flow",
                ).to_deployment(
                    name="persons_storage",
                    description="Stores persons into the database.",
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
