from typing import Literal

from prefect import flow

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.task_orchestration.flows.task_relationship_storage import (
    RelationshipFlow,
)
from src.settings import Settings


@flow(log_prints=True)
def on_permalink_not_found(
    permalink: str,  # entity_type: Literal["Movie", "Person"]
) -> None:
    print(
        f"Ressource with permalink {permalink} not found in storage. Triggering extraction flow."
    )


@flow(name="Relationship Processor Flow")
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
