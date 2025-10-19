import importlib
from datetime import timedelta

from prefect import flow, get_run_logger
from prefect.futures import wait
from prefect.tasks import exponential_backoff

from src.entities.content import TableOfContents
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.tasks.retry import (
    RETRY_ATTEMPTS,
    is_http_task_retriable,
)
from src.repositories.orchestration.tasks.task_downloader import execute_task
from src.repositories.stats import RedisStatsCollector
from src.settings import Settings


@flow(
    name="scrape_flow",
    description="Scrapes Wikipedia pages and stores HTML contents into Redis",
)
def scraping_flow(
    settings: Settings,
    pages: list[TableOfContents],
) -> None:

    logger = get_run_logger()

    http_client = SyncHttpClient(settings=settings)

    # make them unique by page_id
    pages = {p.page_id: p for p in pages}.values()

    tasks = []

    stats_collector = RedisStatsCollector(redis_dsn=settings.redis_stats_dsn)

    # for each page
    for config in pages:

        logger.info(
            f"Processing '{config.__class__.__name__}' with ID '{config.page_id}'"
        )

        module = importlib.import_module("src.entities")

        try:
            cls = getattr(module, config.entity_type)
        except AttributeError as e:
            raise ValueError(f"Unsupported entity type: {config.entity_type}") from e

        html_store = RedisTextStorage[cls](settings=settings)

        tasks.append(
            execute_task.with_options(
                cache_key_fn=lambda *_: f"scraping-{config.page_id}",
                cache_expiration=timedelta(hours=24),
                retries=RETRY_ATTEMPTS,
                # retry_delay_seconds=RETRY_DELAY_SECONDS,
                retry_condition_fn=is_http_task_retriable,
                retry_delay_seconds=exponential_backoff(backoff_factor=0.3),
                retry_jitter_factor=0.1,
                refresh_cache=settings.prefect_cache_disabled,
            ).submit(
                page=config,
                settings=settings,
                http_client=http_client,
                storage_handler=html_store,
                return_results=False,
                stats_collector=stats_collector,
            )
        )

    wait(tasks)
