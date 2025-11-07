from datetime import timedelta
from typing import Literal

from prefect import flow, get_run_logger, task
from prefect.task_runners import ConcurrentTaskRunner

from src.entities.content import TableOfContents
from src.repositories.orchestration.flows.connection import connection_flow
from src.repositories.orchestration.flows.db_storage import db_storage_flow
from src.repositories.orchestration.flows.extract import extract_entities_flow
from src.repositories.orchestration.flows.scraping import scraping_flow
from src.settings import AppSettings

from .hooks import capture_crash_info


@flow(
    name="run_pipeline_for_page",
    description="runs the whole pipeline: scraping, extraction, storage, and connection for a given page.",
    task_runner=ConcurrentTaskRunner(),
    on_crashed=[capture_crash_info],
    log_prints=True,
)
def run_pipeline_for_page(
    entity_type: Literal["Movie", "Person"],
    page_id: str,
    app_settings: AppSettings,
) -> None:
    """
    Runs a full pipeline for a given entity page.
    This flow will download the content, parse it, index it, and store it in the graph database.

    It is triggered on-demand for specific pages/entities.

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
        pages=[page],
        scraping_settings=app_settings.scraping_settings,
        stats_settings=app_settings.stats_settings,
        storage_settings=app_settings.storage_settings,
        prefect_settings=app_settings.prefect_settings,
    )

    extract_task = task(
        cache_key_fn=lambda *_: f"on-demand-extract-{entity_type}-{page_id}",
        cache_expiration=timedelta(hours=1),
    )(extract_entities_flow).submit(
        prefect_settings=app_settings.prefect_settings,
        ml_settings=app_settings.ml_settings,
        section_settings=app_settings.section_settings,
        storage_settings=app_settings.storage_settings,
        stats_settings=app_settings.stats_settings,
        entity_type=entity_type,
        page_id=page_id,
        wait_for=[scraping_task],
    )

    storage_task = task(
        cache_key_fn=lambda *_: f"on-demand-store-{entity_type}-{page_id}",
        cache_expiration=timedelta(hours=1),
    )(db_storage_flow).submit(
        prefect_settings=app_settings.prefect_settings,
        storage_settings=app_settings.storage_settings,
        search_settings=app_settings.search_settings,
        entity_type=entity_type,
        wait_for=[extract_task],
    )

    task(
        cache_key_fn=lambda *_: f"on-demand-connect-{entity_type}-{page_id}",
        cache_expiration=timedelta(hours=1),
    )(connection_flow).submit(
        scraping_settings=app_settings.scraping_settings,
        storage_settings=app_settings.storage_settings,
        prefect_settings=app_settings.prefect_settings,
        entity_type=entity_type,
        wait_for=[storage_task],
    ).wait()

    logger.info(f"Entity '{entity_type}' with page ID '{page_id}' has been connected.")
