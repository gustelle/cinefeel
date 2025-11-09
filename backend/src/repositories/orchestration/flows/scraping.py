from datetime import timedelta
from typing import Literal

from prefect import flow
from prefect.futures import PrefectFuture
from prefect.task_runners import ConcurrentTaskRunner
from prefect.tasks import exponential_backoff

from src.entities import get_entity_class
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.tasks.race import wait_for_all
from src.repositories.orchestration.tasks.retry import (
    RETRY_ATTEMPTS,
    is_http_task_retriable,
)
from src.repositories.orchestration.tasks.task_scraper import execute_task
from src.repositories.stats import RedisStatsCollector
from src.settings import AppSettings

from .hooks import capture_crash_info


@flow(
    name="scrape_flow",
    description="Scrapes Wikipedia pages and stores HTML contents into Redis",
    task_runner=ConcurrentTaskRunner(max_workers=10),
    on_crashed=[capture_crash_info],
    log_prints=False,
)
def scraping_flow(
    app_settings: AppSettings,
    entity_type: Literal["Movie", "Person"],
) -> None:

    http_client = SyncHttpClient(settings=app_settings.scraping_settings)

    pages = [
        p
        for p in app_settings.scraping_settings.start_pages
        if p.entity_type == entity_type
    ]

    # make them unique by page_id
    pages = {p.page_id: p for p in pages}.values()

    tasks: list[PrefectFuture] = []

    stats_collector = RedisStatsCollector(
        redis_dsn=app_settings.stats_settings.redis_dsn
    )
    stats_collector.on_init()

    for _, config in enumerate(pages):

        cls = get_entity_class(config.entity_type)

        html_store = RedisTextStorage[cls](
            redis_dsn=app_settings.storage_settings.redis_dsn
        )
        html_store.on_init()

        tasks.append(
            execute_task.with_options(
                cache_key_fn=lambda *_: f"scraping-{config.page_id}",
                cache_expiration=timedelta(hours=24),
                retries=RETRY_ATTEMPTS,
                retry_condition_fn=is_http_task_retriable,
                retry_delay_seconds=exponential_backoff(backoff_factor=0.3),
                retry_jitter_factor=0.1,
                refresh_cache=app_settings.prefect_settings.cache_disabled,
            ).submit(
                page=config,
                scraping_settings=app_settings.scraping_settings,
                http_client=http_client,
                storage_handler=html_store,
                return_results=False,
                stats_collector=stats_collector,
            )
        )

    wait_for_all(tasks, stats_collector=stats_collector)
