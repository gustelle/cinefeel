import asyncio
from typing import Any

from prefect import Task, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.client.schemas.objects import TaskRun
from prefect.states import State

from src.entities.content import PageLink
from src.interfaces.extractor import IHtmlExtractor
from src.interfaces.http_client import HttpError, IHttpClient
from src.repositories.storage.html_storage import LocalTextStorage
from src.settings import Settings, WikiTOCPageConfig


async def is_retriable(
    task: Task[..., Any], task_run: TaskRun, state: State[Any]
) -> bool:
    logger = get_run_logger()
    try:
        await state.result()
    except Exception as e:
        if isinstance(e, HttpError) and e.status_code >= 429:
            return True
        elif isinstance(e, HttpError):
            logger.warning(
                f"HTTP error with status {e.status_code} will not be retried"
            )
            return False
        else:
            logger.warning(f"Exception is not retriable: {e}")
    return False


@task(
    task_run_name="download_page-{page_id}",
    retries=3,
    retry_delay_seconds=[1, 2, 5],
    retry_condition_fn=is_retriable,
    cache_policy=NO_CACHE,
)
async def download_page(
    page_id: str,
    settings: Settings,
    http_client: IHttpClient,
    storage_handler: LocalTextStorage | None = None,
    return_content: bool = False,
    **params,
) -> str | None:
    """

    Args:
        page_id (str): The page ID to download.
        settings (Settings): The settings object.
        http_client (IHttpClient): The HTTP client to use for downloading.
        storage_handler (HtmlContentStorageHandler | None, optional): The storage handler to use for storing the content. Defaults to None.
        return_content (bool, optional): Whether to return the content. Defaults to False, in which case the content ID is returned.
        **params: Additional parameters for the HTTP request.

    Returns:
        str | None: The content ID if the download was successful, None otherwise.
    """

    endpoint = f"{settings.mediawiki_base_url}/page/{page_id}/html"

    html = await http_client.send(
        url=endpoint,
        response_type="text",
        params=params,
    )

    if html is not None and storage_handler is not None:
        storage_handler.insert(
            content_id=page_id,
            content=html,
        )
    if return_content:
        return html

    return page_id if html is not None else None


@task(cache_policy=NO_CACHE)
async def fetch_page_links(
    config: WikiTOCPageConfig,
    link_extractor: IHtmlExtractor,
    settings: Settings,
    http_client: IHttpClient,
) -> list[PageLink]:
    """
    downloads the HTML pages and returns the list of page IDs.

    Args:
        page (WikiTOCPageConfig): The configuration for the page to be downloaded.

    Returns:
        list[PageLink]: A list of page links.
    """

    logger = get_run_logger()

    html = await download_page(
        page_id=config.page_id,
        settings=settings,
        http_client=http_client,
        return_content=True,  # return the content
    )

    if html is None:
        return []

    # avoid blocking the event loop by using asyncio.to_thread
    try:
        return await asyncio.to_thread(
            link_extractor.retrieve_inner_links,
            html_content=html,
            config=config,
        )

    except Exception as e:
        logger.error(f"Error extracting list of films: {e}")
        return []
