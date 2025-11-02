from datetime import timedelta
from typing import Literal

from prefect import flow, get_run_logger
from prefect.concurrency.sync import concurrency
from prefect.events import emit_event
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
from src.settings import AppSettings

from .hooks import capture_crash_info


@flow(
    name="extract_entities_flow",
    description="Extract entities from HTML contents and store them as JSON.",
    task_runner=ConcurrentTaskRunner(max_workers=10),
    on_crashed=[capture_crash_info],
    log_prints=False,
)
def extract_entities_flow(
    entity_type: Literal["Movie", "Person"],
    app_settings: AppSettings,
    page_id: str | None = None,
    entity_analyzer: IContentAnalyzer | None = None,
    section_searcher: Processor | None = None,
    html_store: IStorageHandler | None = None,
    json_store: IStorageHandler | None = None,
    refresh_cache: bool = False,
) -> None:
    """
    Extract entities (Movie or Person) from HTML contents

    If page_id is provided, only that specific page will be processed. If not, all pages in the HTML storage will be processed.
    Other params are injected for testing purposes.

    Args:
        entity_type (Literal["Movie", "Person"]): The type of entity to extract
        app_settings (AppSettings): Application settings
        page_id (str | None, optional): Specific page ID to process. Defaults to None (process all pages).
        entity_analyzer (IContentAnalyzer | None, optional): Custom entity analyzer
        section_searcher (Processor | None, optional): Custom section searcher
        html_store (IStorageHandler | None, optional): Custom HTML storage handler, defaults to `RedisTextStorage`
        json_store (IStorageHandler | None, optional): Custom JSON storage handler, defaults to `RedisJsonStorage`
        refresh_cache (bool, optional): If True, forces re-processing of all pages by bypassing task cache. Defaults to False.
    """

    logger = get_run_logger()

    cls = get_entity_class(entity_type)

    html_store = RedisTextStorage[cls](app_settings.storage_settings.redis_dsn)
    json_store = RedisJsonStorage[cls](app_settings.storage_settings.redis_dsn)
    stats_collector = RedisStatsCollector(app_settings.stats_settings.redis_dsn)

    html_store.on_init()
    stats_collector.on_init()
    json_store.on_init()

    _refresh_cache = app_settings.prefect_settings.cache_disabled or refresh_cache

    if page_id:
        content = html_store.select(content_id=page_id)

        if content:

            with concurrency("heavy", occupy=1):

                execute_task.with_options(
                    retries=RETRY_ATTEMPTS,
                    retry_delay_seconds=RETRY_DELAY_SECONDS,
                    cache_key_fn=lambda *_: f"html-to-entity-{page_id}",
                    cache_expiration=timedelta(hours=24),
                    timeout_seconds=60 * 10,  # 10 minutes
                    refresh_cache=_refresh_cache,
                    tags=["heavy"],  # mark as heavy task
                ).submit(
                    content_id=page_id,
                    content=content,
                    output_storage=json_store,
                    section_settings=app_settings.section_settings,
                    ml_settings=app_settings.ml_settings,
                    entity_type=cls,
                    analyzer=entity_analyzer,
                    search_processor=section_searcher,
                    stats_collector=stats_collector,
                )

        else:
            # request extraction flow via event if content not found
            emit_event(
                event="extract.entity",
                resource={"prefect.resource.id": page_id},
                payload={"entity_type": entity_type},
            )
    else:

        with concurrency("heavy", occupy=1):

            for content_id, content in html_store.scan():
                if not content or not content_id:
                    logger.warning(
                        f"Skipping empty content or content_id: '{content_id}'"
                    )
                    continue

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
                    ml_settings=app_settings.ml_settings,
                    section_settings=app_settings.section_settings,
                    entity_type=cls,
                    analyzer=entity_analyzer,
                    search_processor=section_searcher,
                    stats_collector=stats_collector,
                )
            # count += 1
            # if count >= 10:
            #     break  # for testing, process only one

    # print(f"Waiting for {len(tasks)} tasks to complete...")
    # wait_for_all(tasks)
