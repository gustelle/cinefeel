from datetime import timedelta
from typing import Literal

from prefect import flow, get_run_logger
from prefect.events import emit_event
from prefect.futures import PrefectFuture, wait
from prefect.task_runners import ConcurrentTaskRunner

from src.entities import get_entity_class
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.nlp_processor import Processor
from src.interfaces.storage import IStorageHandler
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.tasks.retry import (
    RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
)
from src.repositories.orchestration.tasks.task_html_parsing import execute_task
from src.repositories.stats import RedisStatsCollector
from src.settings import Settings

from .hooks import capture_crash_info


@flow(
    name="extract_entities",
    description="Extract entities (Movie or Person) from HTML contents",
    task_runner=ConcurrentTaskRunner(),
    on_crashed=[capture_crash_info],
    log_prints=True,
)
def extract_entities_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
    page_id: str | None = None,
    # for testing purposes, we can inject a custom things
    entity_analyzer: IContentAnalyzer | None = None,
    section_searcher: Processor | None = None,
    html_store: IStorageHandler | None = None,
    json_store: IStorageHandler | None = None,
    refresh_cache: bool = False,
) -> None:
    """
    Extract entities (Movie or Person) from HTML contents

    for technical reasons (Prefect serialization) we use `Literal["Movie", "Person"]` as entity_type
    they are just mapped to the Movie and Person classes respectively.

    If page_id is provided, only that specific page will be processed. If not, all pages in the HTML storage will be processed.
    Other params are injected for testing purposes.

    Args:
        settings (Settings): Application settings.
        entity_type (Literal["Movie", "Person"]): Type of entity to extract.
        page_id (str | None, optional): Specific page ID to process. Defaults to None (process all pages).
        entity_analyzer (IContentAnalyzer | None, optional): Custom entity analyzer
        section_searcher (Processor | None, optional): Custom section searcher
        html_store (IStorageHandler | None, optional): Custom HTML storage handler, defaults to `RedisTextStorage`
        json_store (IStorageHandler | None, optional): Custom JSON storage handler, defaults to `RedisJsonStorage`
        refresh_cache (bool, optional): If True, forces re-processing of all pages by bypassing task cache. Defaults to False.
    """

    tasks: list[PrefectFuture] = []

    logger = get_run_logger()

    cls = get_entity_class(entity_type)

    html_store = html_store or RedisTextStorage[cls](settings=settings)
    json_store = json_store or RedisJsonStorage[cls](settings=settings)

    stats_collector = RedisStatsCollector(redis_dsn=settings.redis_stats_dsn)

    _refresh_cache = settings.prefect_cache_disabled or refresh_cache

    logger.info(
        f"Starting extraction flow for entity_type={entity_type}, page_id={page_id}, refresh_cache={_refresh_cache}"
    )

    if page_id:
        content = html_store.select(content_id=page_id)

        if content:
            execute_task.with_options(
                retries=RETRY_ATTEMPTS,
                retry_delay_seconds=RETRY_DELAY_SECONDS,
                cache_key_fn=lambda *_: f"html-to-entity-{page_id}",
                cache_expiration=timedelta(seconds=1),
                timeout_seconds=60 * 10,  # 10 minutes
                refresh_cache=_refresh_cache,
            ).submit(
                content_id=page_id,
                content=content,
                output_storage=json_store,
                settings=settings,
                entity_type=cls,
                analyzer=entity_analyzer,
                search_processor=section_searcher,
                stats_collector=stats_collector,
            ).wait()
        else:
            # request extraction flow via event if content not found
            emit_event(
                event="extract.entity",
                resource={"prefect.resource.id": page_id},
                payload={"entity_type": entity_type},
            )
    else:
        # count = 0
        # iterate over all HTML contents in Redis
        for content_id, content in html_store.scan():
            if not content or not content_id:
                logger.warning(f"Skipping empty content or content_id: '{content_id}'")
                continue

            tasks.append(
                execute_task.with_options(
                    retries=RETRY_ATTEMPTS,
                    retry_delay_seconds=RETRY_DELAY_SECONDS,
                    cache_key_fn=lambda *_: f"parser_execute_task-{content_id}",
                    cache_expiration=timedelta(minutes=5),
                    timeout_seconds=60 * 5,  # 5 minutes
                    refresh_cache=_refresh_cache,
                    tags=["heavy"],  # mark as heavy task
                ).submit(
                    content_id=content_id,
                    content=content,
                    output_storage=json_store,
                    settings=settings,
                    entity_type=cls,
                    analyzer=entity_analyzer,
                    search_processor=section_searcher,
                    stats_collector=stats_collector,
                )
            )
            # count += 1
            # if count >= :
            #     break  # for testing, process only one

        # timeout is set at task level
        wait(tasks)
