from pathlib import Path

from prefect import deploy, flow
from prefect.events import DeploymentEventTrigger

from src.entities.movie import Movie
from src.entities.person import Person
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
                entrypoint="connection.py:extract_entity_from_page",
            ).to_deployment(
                name="extract_entity_from_page",
                description="Triggers when an entity is not found in the storage which will trigger the extraction flow.",
                triggers=[
                    DeploymentEventTrigger(
                        enabled=True,
                        expect={"extract.entity"},
                        parameters={
                            "page_id": "{{ event.resource.id }}",
                            "entity_type": "{{ event.payload.entity_type }}",
                            "settings": self.settings,
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
                        "settings": self.settings,
                        "entity_type": Movie.__name__,
                    },
                    concurrency_limit=self.settings.prefect_flows_concurrency_limit,
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
                        "entity_type": Person.__name__,
                    },
                    concurrency_limit=self.settings.prefect_flows_concurrency_limit,
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
