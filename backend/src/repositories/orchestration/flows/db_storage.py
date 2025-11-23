from datetime import timedelta
from typing import Literal

from prefect import flow
from prefect.futures import wait
from prefect.tasks import exponential_backoff

from src.entities import get_entity_class
from src.entities.movie import Movie
from src.interfaces.storage import IRelationshipHandler, IStorageHandler
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.orchestration.tasks.task_storage import execute_task
from src.repositories.search.meili_indexer import MeiliHandler
from src.settings import AppSettings


@flow(
    name="db_storage_flow",
    description="Store extracted entities into a storage backend.",
)
def db_storage_flow(
    app_settings: AppSettings,
    entity_type: Literal["Movie", "Person"],
    # for testing purposes, we can inject custom storage handlers
    json_store: IStorageHandler | None = None,
    graph_store: IRelationshipHandler | None = None,
    search_store: IStorageHandler | None = None,
    refresh_cache: bool = False,
) -> None:

    cls = get_entity_class(entity_type)

    json_store = json_store or RedisJsonStorage[cls](
        redis_dsn=app_settings.storage_settings.redis_dsn
    )

    json_store.on_init()

    graph_store = graph_store or (
        MovieGraphRepository(settings=app_settings.storage_settings)
        if cls is Movie
        else PersonGraphRepository(settings=app_settings.storage_settings)
    )

    graph_store.on_init()

    search_handler = search_store or MeiliHandler[cls](
        settings=app_settings.search_settings
    )

    search_handler.on_init()

    t = execute_task.with_options(
        retries=app_settings.prefect_settings.task_retry_attempts,
        retry_delay_seconds=exponential_backoff(
            backoff_factor=app_settings.prefect_settings.task_retry_backoff_factor
        ),
        cache_expiration=timedelta(
            hours=app_settings.prefect_settings.task_cache_expiration_hours
        ),
        timeout_seconds=1,  # fail fast if the task hangs
        cache_key_fn=lambda *_: f"insert_task-json-graph-{entity_type}",
        refresh_cache=app_settings.prefect_settings.cache_disabled or refresh_cache,
    ).submit(
        input_storage=json_store,
        output_storage=graph_store,
    )

    # for all pages
    u = execute_task.with_options(
        retries=app_settings.prefect_settings.task_retry_attempts,
        retry_delay_seconds=exponential_backoff(
            backoff_factor=app_settings.prefect_settings.task_retry_backoff_factor
        ),
        cache_expiration=timedelta(
            hours=app_settings.prefect_settings.task_cache_expiration_hours
        ),
        cache_key_fn=lambda *_: f"insert_task-json-search-{entity_type}",
        timeout_seconds=1,  # fail fast if the task hangs
        refresh_cache=app_settings.prefect_settings.cache_disabled or refresh_cache,
    ).submit(input_storage=json_store, output_storage=search_handler)

    wait([t, u])  # wait for all tasks to complete
