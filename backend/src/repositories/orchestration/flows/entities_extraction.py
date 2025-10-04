import importlib
from typing import Literal

from prefect import flow, get_run_logger
from prefect.cache_policies import INPUTS, NO_CACHE
from prefect.futures import PrefectFuture, wait
from prefect.locking.memory import MemoryLockManager
from prefect.task_runners import ConcurrentTaskRunner
from prefect.transactions import IsolationLevel

from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.nlp_processor import Processor
from src.interfaces.storage import IStorageHandler
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.tasks.retry import (
    RETRY_ATTEMPTS,
    RETRY_DELAY_SECONDS,
    is_task_retriable,
)
from src.repositories.orchestration.tasks.task_html_parsing import HtmlDataParserTask
from src.settings import Settings

cache_policy = INPUTS.configure(
    isolation_level=IsolationLevel.SERIALIZABLE,
    lock_manager=MemoryLockManager(),
)


@flow(
    name="extract_entities",
    description="Extract entities (Movie or Person) from HTML contents",
    task_runner=ConcurrentTaskRunner(),
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
    """

    tasks: list[PrefectFuture] = []

    logger = get_run_logger()

    module = importlib.import_module("src.entities")

    try:
        cls = getattr(module, entity_type)
    except AttributeError as e:
        raise ValueError(f"Unsupported entity type: {entity_type}") from e

    parser_task = HtmlDataParserTask(
        settings=settings,
        entity_type=cls,
        analyzer=entity_analyzer,
        search_processor=section_searcher,
    )

    html_store = html_store or RedisTextStorage(settings=settings)
    json_store = json_store or RedisJsonStorage[cls](settings=settings)

    if page_id:
        content = html_store.select(content_id=page_id)
        if content:
            parser_task.execute.with_options(
                retries=RETRY_ATTEMPTS,
                retry_delay_seconds=RETRY_DELAY_SECONDS,
                retry_condition_fn=is_task_retriable,
                cache_policy=NO_CACHE,
                # cache_expiration=60 * 60 * 24,  # 24 hours
                tags=["cinefeel_tasks"],
                timeout_seconds=180,
            ).submit(
                content_id=page_id,
                content=content,
                output_storage=json_store,
            ).wait()
        else:
            raise ValueError(f"No HTML content found for page_id: '{page_id}'")
    else:
        # iterate over all HTML contents in Redis
        for content_id, content in html_store.scan():
            if not content or not content_id:
                logger.warning(f"Skipping empty content or content_id: '{content_id}'")
                continue

            tasks.append(
                parser_task.execute.with_options(
                    retries=RETRY_ATTEMPTS,
                    retry_delay_seconds=RETRY_DELAY_SECONDS,
                    retry_condition_fn=is_task_retriable,
                    cache_policy=NO_CACHE,
                    # cache_expiration=60 * 60 * 24,  # 24 hours
                    tags=["cinefeel_tasks"],
                    timeout_seconds=180,
                ).submit(
                    content_id=content_id,
                    content=content,
                    output_storage=json_store,
                )
            )

            # break  # for testing, process only one

        logger.info(f"Submitted {len(tasks)} tasks for entity extraction.")

        # timeout is set at task level
        wait(tasks)
