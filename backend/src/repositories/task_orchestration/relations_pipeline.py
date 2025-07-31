from typing import Literal

from prefect import Flow, flow, get_run_logger
from prefect.client.schemas import FlowRun, State

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.task_orchestration.flows.task_relationship_storage import (
    RelationshipFlow,
)
from src.settings import Settings


def relationship_failure_handler(flow: Flow, flow_run: FlowRun, state: State) -> None:
    """
    Handles failures in the relationship processing flow.
    This function can be used to log errors or perform cleanup actions.

    TODO:
    - trigger a unit extraction of the  entity
    """
    get_run_logger().error("-" * 40)
    get_run_logger().error("Relationship processing flow failed.")
    get_run_logger().error(flow)
    get_run_logger().error(flow_run)
    get_run_logger().error(state)
    get_run_logger().error("-" * 40)


@flow(name="Relationship Processor Flow", on_failure=[relationship_failure_handler])
def relationship_processor_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
) -> None:
    """
    Reads Entities (Film or Person) from the storage,
    and analyzes their content to identify relationships between them.
    """

    match entity_type:
        case "Movie":
            entity_type = Film
        case "Person":

            entity_type = Person
        case _:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    http_client = SyncHttpClient(settings=settings)

    # where to store the relationships
    db_storage = (
        FilmGraphHandler(
            settings=settings,
        )
        if entity_type is Film
        else PersonGraphHandler(
            settings=settings,
        )
    )

    RelationshipFlow(
        settings=settings,
        http_client=http_client,
    ).execute(
        input_storage=db_storage,
        output_storage=db_storage,
    )
