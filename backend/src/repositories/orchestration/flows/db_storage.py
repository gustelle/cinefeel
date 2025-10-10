import importlib
from typing import Literal

from prefect import flow
from prefect.futures import wait

from src.entities.movie import Movie
from src.interfaces.storage import IStorageHandler
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.orchestration.tasks.retry import (
    RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
)
from src.repositories.orchestration.tasks.task_storage import execute_task
from src.repositories.search.meili_indexer import MeiliHandler
from src.settings import Settings


@flow(
    name="db_storage_flow",
    description="Store extracted entities into a storage backend.",
)
def db_storage_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
    # for testing purposes, we can inject custom storage handlers
    json_store: IStorageHandler | None = None,
    graph_store: IStorageHandler | None = None,
    search_store: IStorageHandler | None = None,
    refresh_cache: bool = False,
) -> None:

    module = importlib.import_module("src.entities")

    try:
        cls = getattr(module, entity_type)
    except AttributeError as e:
        raise ValueError(f"Unsupported entity type: {entity_type}") from e

    json_store = json_store or RedisJsonStorage[cls](settings=settings)

    graph_store = graph_store or (
        MovieGraphRepository(settings=settings)
        if cls is Movie
        else PersonGraphRepository(settings=settings)
    )

    search_handler = search_store or MeiliHandler[cls](settings=settings)

    t = execute_task.with_options(
        retries=RETRY_ATTEMPTS,
        retry_delay_seconds=RETRY_DELAY_SECONDS,
        tags=["cinefeel_tasks"],
        timeout_seconds=1,  # fail fast if the task hangs
        cache_key_fn=lambda *_: f"insert_task-json-graph-{entity_type}",
        refresh_cache=refresh_cache,
    ).submit(
        input_storage=json_store,
        output_storage=graph_store,
    )

    # for all pages
    u = execute_task.with_options(
        retries=RETRY_ATTEMPTS,
        retry_delay_seconds=RETRY_DELAY_SECONDS,
        cache_key_fn=lambda *_: f"insert_task-json-search-{entity_type}",
        tags=["cinefeel_tasks"],
        timeout_seconds=1,  # fail fast if the task hangs
        refresh_cache=refresh_cache,
    ).submit(input_storage=json_store, output_storage=search_handler)

    wait([t, u])  # wait for all tasks to complete
