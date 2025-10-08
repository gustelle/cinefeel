from __future__ import annotations

import importlib
from typing import Literal

from prefect import flow, get_run_logger, task

from src.entities.content import TableOfContents
from src.interfaces.storage import IStorageHandler
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.flows.db_storage import db_storage_flow
from src.repositories.orchestration.flows.entities_extraction import (
    extract_entities_flow,
)
from src.repositories.orchestration.flows.scraping import scraping_flow
from src.repositories.orchestration.tasks.retry import (
    RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
)
from src.repositories.orchestration.tasks.task_relationship_storage import (
    EntityRelationshipTask,
)
from src.settings import Settings


@flow(
    name="extract_entity_from_page",
    description="Based on the entity type and page_id, this flow will extract the entity and store it in the database.",
)
def extract_entity_from_page(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
    page_id: str,
) -> None:
    """
    Extract an entity (Movie or Person) from a given permalink.
    This flow will download the content, parse it, index it, and store it in the graph database.

    It is useful when making a relationship between two entities, and one of them is not existing yet in the database.
    typically, it is triggered on-demand by the connection workflow.

    """
    logger = get_run_logger()

    page = TableOfContents(
        page_id=page_id,
        entity_type=entity_type,
    )

    logger.info(f"Downloading '{entity_type}' for page_id: {page_id}")

    scraping_task = task()(scraping_flow).submit(
        settings=settings,
        pages=[page],
    )

    extract_task = task()(extract_entities_flow).submit(
        settings=settings,
        entity_type=entity_type,
        page_id=page_id,
        wait_for=[scraping_task],
    )

    storage_task = task()(db_storage_flow).submit(
        settings=settings,
        entity_type=entity_type,
        wait_for=[extract_task],
    )

    task()(connection_flow).submit(
        settings=settings,
        entity_type=entity_type,
        wait_for=[storage_task],
    ).wait()

    logger.info(f"Entity '{entity_type}' with page ID '{page_id}' has been connected.")


@flow(name="connection_flow")
def connection_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
    # for testing purposes, we can inject custom storage handlers
    graph_store: IStorageHandler | None = None,
) -> None:
    """
    Reads Entities (Movie or Person) from the storage,
    and analyzes their content to identify connections between them.

    """

    module = importlib.import_module("src.entities")

    try:
        getattr(module, entity_type)
    except AttributeError as e:
        raise ValueError(f"Unsupported entity type: {entity_type}") from e

    http_client = SyncHttpClient(settings=settings)

    # where to store the relationships
    db_storage = graph_store or (
        MovieGraphRepository(
            settings=settings,
        )
        if entity_type == "Movie"
        else PersonGraphRepository(
            settings=settings,
        )
    )

    EntityRelationshipTask(
        settings=settings,
        http_client=http_client,
    ).execute.with_options(
        retries=RETRY_ATTEMPTS,
        retry_delay_seconds=RETRY_DELAY_SECONDS,
        # cache_policy=CACHE_POLICY,
        cache_expiration=60 * 60 * 1,  # 1 hour
        cache_key_fn=lambda *_: f"execute-connection-{entity_type}",
        tags=["cinefeel_tasks"],
    ).submit(
        input_storage=db_storage,
        output_storage=db_storage,
    ).wait()
