import importlib
from typing import Literal

from prefect import flow
from prefect.cache_policies import NO_CACHE
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
from src.repositories.orchestration.tasks.task_storage import BatchInsertTask
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

    insert_task = BatchInsertTask(
        settings=settings,
        entity_type=cls,
    )

    t = insert_task.execute.with_options(
        retries=RETRY_ATTEMPTS,
        retry_delay_seconds=RETRY_DELAY_SECONDS,
        cache_policy=NO_CACHE,
        # cache_expiration=60 * 60 * 24,  # 24 hours
        tags=["cinefeel_tasks"],
        timeout_seconds=1,  # fail fast if the task hangs
    ).submit(
        input_storage=json_store,
        output_storage=graph_store,
    )

    # for all pages
    u = insert_task.execute.with_options(
        retries=RETRY_ATTEMPTS,
        retry_delay_seconds=RETRY_DELAY_SECONDS,
        cache_policy=NO_CACHE,
        # cache_expiration=60 * 60 * 24,  # 24 hours
        tags=["cinefeel_tasks"],
        timeout_seconds=1,  # fail fast if the task hangs
    ).submit(input_storage=json_store, output_storage=search_handler)

    wait([t, u])  # wait for all tasks to complete
