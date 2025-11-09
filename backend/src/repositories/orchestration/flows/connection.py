from datetime import timedelta
from typing import Literal

from prefect import flow, get_run_logger
from prefect.concurrency.sync import rate_limit
from prefect.futures import PrefectFuture
from prefect.task_runners import ConcurrentTaskRunner

from src.entities import get_entity_class
from src.interfaces.storage import IRelationshipHandler, IStorageHandler
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.tasks.race import wait_for_all
from src.repositories.orchestration.tasks.retry import RETRY_DELAY_SECONDS
from src.repositories.orchestration.tasks.task_relationship import execute_task
from src.settings import AppSettings

from .hooks import capture_crash_info


@flow(
    name="connection_flow",
    description="Link entities based on their relationships.",
    task_runner=ConcurrentTaskRunner(),
    on_crashed=[capture_crash_info],
    log_prints=False,
)
def connection_flow(
    entity_type: Literal["Movie", "Person"],
    app_settings: AppSettings,
    # for testing purposes, we can inject custom storage handlers
    input_store: IStorageHandler | None = None,
    graph_store: IRelationshipHandler | None = None,
) -> None:
    """
    Reads Entities (Movie or Person) from the storage,
    and analyzes their content to identify connections between them.

    Args:
        app_settings (AppSettings): Application settings containing various configurations.
        entity_type (Literal["Movie", "Person"]): Type of entity to process.
        input_store (IStorageHandler | None, optional): Custom input storage handler, defaults to `RedisJsonStorage`.
        graph_store (IStorageHandler | None, optional): Custom graph storage handler, defaults to `MovieGraphRepository` or `PersonGraphRepository`.

    """

    logger = get_run_logger()

    cls = get_entity_class(entity_type)

    tasks: list[PrefectFuture] = []

    http_client = SyncHttpClient(settings=app_settings.scraping_settings)

    store = input_store or RedisJsonStorage[cls](
        app_settings.storage_settings.redis_dsn
    )

    # where to store the relationships
    db_storage = graph_store or (
        MovieGraphRepository(
            settings=app_settings.storage_settings,
        )
        if entity_type == "Movie"
        else PersonGraphRepository(
            settings=app_settings.storage_settings,
        )
    )

    for entity_id, entity in store.scan():
        if not entity or not entity_id:
            logger.warning(f"Skipping empty entity or entity_id: '{entity_id}'")
            continue

        rate_limit("resource-rate-limiting", occupy=1)

        tasks.append(
            execute_task.with_options(
                retries=3,
                retry_delay_seconds=RETRY_DELAY_SECONDS,
                cache_expiration=timedelta(hours=24),
                cache_key_fn=lambda *_: f"connection_task-{entity_id}",
                refresh_cache=app_settings.prefect_settings.cache_disabled,
            ).submit(
                entity=entity,
                output_storage=db_storage,
                http_client=http_client,
            )
        )

    # wait for all tasks to complete
    wait_for_all(tasks)
