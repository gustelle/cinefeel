from __future__ import annotations

from datetime import timedelta
from typing import Literal

from prefect import flow, get_run_logger, task
from prefect.futures import PrefectFuture, wait
from prefect.task_runners import ConcurrentTaskRunner

from src.entities import get_entity_class
from src.entities.content import TableOfContents
from src.interfaces.storage import IStorageHandler
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.flows.db_storage import db_storage_flow
from src.repositories.orchestration.flows.extract import extract_entities_flow
from src.repositories.orchestration.flows.scraping import scraping_flow
from src.repositories.orchestration.tasks.retry import (
    RETRY_DELAY_SECONDS,
)
from src.repositories.orchestration.tasks.task_relationship import execute_task
from src.settings import Settings

from .hooks import capture_crash_info


@flow(
    name="extract_entity_from_page",
    description="Based on the entity type and page_id, this flow will extract the entity and store it in the database.",
    task_runner=ConcurrentTaskRunner(),
    on_crashed=[capture_crash_info],
    log_prints=True,
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

    scraping_task = task(
        cache_key_fn=lambda *_: f"on-demand-scraping-{page_id}",
        cache_expiration=timedelta(hours=1),
    )(scraping_flow).submit(
        settings=settings,
        pages=[page],
    )

    extract_task = task(
        cache_key_fn=lambda *_: f"on-demand-extract-{entity_type}-{page_id}",
        cache_expiration=timedelta(hours=1),
    )(extract_entities_flow).submit(
        settings=settings,
        entity_type=entity_type,
        page_id=page_id,
        wait_for=[scraping_task],
    )

    storage_task = task(
        cache_key_fn=lambda *_: f"on-demand-store-{entity_type}-{page_id}",
        cache_expiration=timedelta(hours=1),
    )(db_storage_flow).submit(
        settings=settings,
        entity_type=entity_type,
        wait_for=[extract_task],
    )

    task(
        cache_key_fn=lambda *_: f"on-demand-connect-{entity_type}-{page_id}",
        cache_expiration=timedelta(hours=1),
    )(connection_flow).submit(
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
    input_store: IStorageHandler | None = None,
    graph_store: IStorageHandler | None = None,
) -> None:
    """
    Reads Entities (Movie or Person) from the storage,
    and analyzes their content to identify connections between them.

    Args:
        settings (Settings): Application settings.
        entity_type (Literal["Movie", "Person"]): Type of entity to process.
        input_store (IStorageHandler | None, optional): Custom input storage handler, defaults to `RedisJsonStorage`.
        graph_store (IStorageHandler | None, optional): Custom graph storage handler, defaults to `MovieGraphRepository` or `PersonGraphRepository`.

    """

    logger = get_run_logger()

    tasks: list[PrefectFuture] = []

    logger.info(
        f"Starting connection flow for entity_type={entity_type} (cache disabled={settings.prefect_cache_disabled})"
    )

    cls = get_entity_class(entity_type)

    http_client = SyncHttpClient(settings=settings)

    store = input_store or RedisJsonStorage[cls](settings=settings)

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

    for entity_id, entity in store.scan():
        if not entity or not entity_id:
            logger.warning(f"Skipping empty entity or entity_id: '{entity_id}'")
            continue

        tasks.append(
            execute_task.with_options(
                retries=3,
                retry_delay_seconds=RETRY_DELAY_SECONDS,
                cache_expiration=timedelta(hours=24),
                cache_key_fn=lambda *_: f"connection_task-{entity_id}",
                refresh_cache=settings.prefect_cache_disabled,
            ).submit(
                entity=entity,
                output_storage=db_storage,
                settings=settings,
                http_client=http_client,
            )
        )

    # timeout is set at task level
    wait(tasks)
