import importlib

from prefect import flow, get_run_logger
from prefect.futures import wait

from src.entities.content import TableOfContents
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.tasks.retry import (
    RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
    is_task_retriable,
)
from src.repositories.orchestration.tasks.task_downloader import ContentDownloaderTask
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

    download_task = ContentDownloaderTask(settings=settings, http_client=http_client)

    # make them unique by page_id
    pages = {p.page_id: p for p in pages}.values()

    tasks = []

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
            download_task.execute.with_options(
                retries=RETRY_ATTEMPTS,
                retry_delay_seconds=RETRY_DELAY_SECONDS,
                retry_condition_fn=is_task_retriable,
                tags=["cinefeel_tasks"],
                timeout_seconds=30,
            ).submit(
                page=config,
                storage_handler=html_store,
                return_results=False,
            )
        )

    wait(tasks)
