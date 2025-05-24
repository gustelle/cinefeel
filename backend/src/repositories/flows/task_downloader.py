import asyncio
from typing import Any

from prefect import Task, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.client.schemas.objects import TaskRun
from prefect.states import State

from src.entities.content import WikiPageLink
from src.interfaces.extractor import IHtmlExtractor
from src.interfaces.http_client import HttpError, IHttpClient
from src.repositories.storage.html_storage import LocalTextStorage
from src.settings import Settings, WikiTOCPageConfig


def is_retriable(task: Task[..., Any], task_run: TaskRun, state: State[Any]) -> bool:
    try:
        state.result()
    except Exception as e:
        if isinstance(e, HttpError) and e.status_code >= 429:
            return True
    return False


@task(
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
    TODO:
    - testing: what happens after 3 retries?
    - verify no retrty on 404, 429

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
        endpoint=endpoint,
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
async def fetch_wiki_page_links(
    page: WikiTOCPageConfig,
    link_extractor: IHtmlExtractor,
    settings: Settings,
    http_client: IHttpClient,
) -> list[WikiPageLink]:
    """
    downloads the HTML pages and returns the list of page IDs.

    TODO:
    - retrieve_inner_links with dramatiq not dask which is not intended for this
    - testing of case where an exception is raised in one of the tasks
    - use a dramatiq or dask worker to run the tasks in parallel

    Args:
        page (WikiTOCPageConfig): The page to download.

    Returns:
        list[WikiPageLink]: A list of page links.
    """

    logger = get_run_logger()

    html = await download_page(
        page_id=page.page_id,
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
            css_selector=page.toc_css_selector,
        )

    except Exception as e:
        logger.error(f"Error extracting list of films: {e}")
        return []
