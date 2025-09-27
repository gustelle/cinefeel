from __future__ import annotations

from typing import Literal

from prefect import flow, get_run_logger, task

from src.entities.content import TableOfContents
from src.entities.movie import Movie
from src.entities.person import Person
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.flows.db_storage import db_storage_flow
from src.repositories.orchestration.flows.entities_extraction import (
    extract_entities_flow,
)
from src.repositories.orchestration.flows.scraping import scraping_flow
from src.repositories.orchestration.tasks.task_relationship_storage import (
    EntityRelationshipTask,
)
from src.settings import Settings


@flow(
    name="process_entity_extraction",
    description="Based on the entity type and page_id, this flow will extract the entity and store it in the database.",
)
def process_entity_extraction(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
    page_id: str,
) -> None:
    """
    Extract a single entity (Movie or Person) from a given permalink.
    This flow will download the content, parse it, index it, and store it in the graph database.

    It is quite useful when making a relationship between two entities, and one of them is not existing yet in the database.
    typically, it is triggered on-demand by the relationship workflow.

    """
    logger = get_run_logger()

    # page_id = permalink.split("/")[-1]  # Extract page ID from permalink

    page = TableOfContents(
        page_id=page_id,
        entity_type=entity_type,
    )

    logger.info(f"Downloading '{entity_type}' for page_id: {page_id}")

    task()(scraping_flow).submit(
        settings=settings,
        pages=[page],
    ).wait()

    # sanitize page_id to be used as a filename
    # page_id = re.sub(r"[^a-zA-Z0-9_-]", "_", page_id)

    logger.info(
        f"Downloaded '{entity_type}' with page ID '{page_id}', now running the extraction flow."
    )

    task()(extract_entities_flow).submit(
        settings=settings,
        entity_type=entity_type,
        page_id=page_id,
    ).wait()

    logger.info(
        f"Extracted '{entity_type}' with page ID '{page_id}', now running the storage flow."
    )

    task()(db_storage_flow).submit(
        settings=settings,
        entity_type=entity_type,
    ).wait()

    logger.info(
        f"Entity '{entity_type}' with page ID '{page_id}' has been processed. Now entering the connection flow."
    )

    task()(connection_flow).submit(
        settings=settings,
        entity_type=entity_type,
    ).wait()

    logger.info(f"Entity '{entity_type}' with page ID '{page_id}' has been connected.")


@flow(name="connection_flow")
def connection_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
) -> None:
    """
    Reads Entities (Movie or Person) from the storage,
    and analyzes their content to identify connections between them.

    TODO:
    - mark entities as "processed" to avoid re-processing them
    - pass a param to re-process all entities if needed (a bit like a "force
    """

    match entity_type:
        case "Movie":
            _entity_type = Movie
        case "Person":

            _entity_type = Person
        case _:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    http_client = SyncHttpClient(settings=settings)

    # where to store the relationships
    db_storage = (
        MovieGraphRepository(
            settings=settings,
        )
        if _entity_type is Movie
        else PersonGraphRepository(
            settings=settings,
        )
    )

    EntityRelationshipTask(
        settings=settings,
        http_client=http_client,
    ).execute.submit(
        input_storage=db_storage,
        output_storage=db_storage,
    ).wait()
