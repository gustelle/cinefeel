from pathlib import Path

from prefect import deploy, flow
from prefect.events import DeploymentEventTrigger

from src.entities.movie import Movie
from src.entities.person import Person
from src.settings import AppSettings

from .uc_types import EntityType


class EntitiesConnectionUseCase:

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

        _flows = [
            flow.from_source(
                source=Path(__file__).parent.parent
                / "repositories/orchestration/flows",
                entrypoint="pipeline.py:run_pipeline_for_page",
            ).to_deployment(
                name="run_pipeline_for_page",
                description="Triggers when an entity is not found in the storage which will trigger the extraction flow.",
                triggers=[
                    DeploymentEventTrigger(
                        enabled=True,
                        expect={"extract.entity"},
                        parameters={
                            "page_id": "{{ event.resource.id }}",
                            "entity_type": "{{ event.payload.entity_type }}",
                            "app_settings": self._app_settings,
                        },
                    )
                ],
                concurrency_limit=10,  # max 10 at a time
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
                    entrypoint="connection.py:connection_flow",
                ).to_deployment(
                    name="persons_connection",
                    description="Adds connections to persons.",
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
