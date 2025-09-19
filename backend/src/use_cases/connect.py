from pathlib import Path

from prefect import deploy, flow
from prefect.events import DeploymentEventTrigger

from src.settings import Settings

from .uc_types import EntityType


class EntitiesConnectionUseCase:

    settings: Settings
    _types: list[EntityType]

    def __init__(self, settings: Settings, types: list[EntityType]):
        self.settings = settings
        self._types = types

    def execute(self):

        _flows = [
            flow.from_source(
                source=Path(__file__).parent.parent
                / "repositories/orchestration/flows",
                entrypoint="connection.py:on_permalink_not_found",
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
                    "working_dir": Path(__file__)
                    .parent.parent.parent.resolve()
                    .as_posix(),
                },
            )
        ]

        if "movies" in self._types:

            _flows.append(
                flow.from_source(
                    source=Path(__file__).parent.parent
                    / "repositories/orchestration/flows",
                    entrypoint="connection.py:connection_flow",
                ).to_deployment(
                    name="movies_connection",
                    description="Adds connections to movies.",
                    parameters={
                        "settings": self.settings,
                        "entity_type": "Movie",
                    },
                    cron="00 08 * * *",  # Every day at 8:00 AM
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
                    entrypoint="connection.py:connection_flow",
                ).to_deployment(
                    name="persons_connection",
                    description="Adds connections to persons.",
                    parameters={
                        "settings": self.settings,
                        "entity_type": "Person",
                    },
                    cron="00 09 * * *",  # Every day at 9:00 AM
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
