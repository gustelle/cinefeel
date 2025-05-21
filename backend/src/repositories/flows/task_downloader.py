import asyncio
from typing import Any

from prefect import Task, flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.client.schemas.objects import TaskRun
from prefect.states import State

from src.entities.film import Film
from src.entities.wiki import WikiPageLink
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.link_extractor import ILinkExtractor
from src.repositories.html_parser.wikipedia_extractor import WikipediaLinkExtractor
from src.repositories.http.async_http import AsyncHttpClient
from src.repositories.storage.html_storage import HtmlContentStorageHandler
from src.settings import Settings, WikiTOCPageConfig

CONCURRENCY = 4


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
    storage_handler: HtmlContentStorageHandler | None = None,
    **params,
) -> str | None:
    """
    Get raw HTML from the Wikipedia API.

    Args:
        page_id (str): The wikipedia ID of the page to download.
        storage_handler (IStorageHandler, optional): The storage handler to use. Defaults to None.
            If not provided, no storage will be performed.
    """

    page_endpoint: str = "page/"

    endpoint = f"{settings.mediawiki_base_url}/{page_endpoint}{page_id}/html"

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

    return html


@task(cache_policy=NO_CACHE)
async def fetch_wiki_page_links(
    page: WikiTOCPageConfig,
    link_extractor: ILinkExtractor,
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
        page_id=page.page_id, settings=settings, http_client=http_client
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


@flow()
async def download_film_pages(
    settings: Settings,
) -> None:

    logger = get_run_logger()

    storage_handler = HtmlContentStorageHandler[Film](
        path=settings.persistence_directory,
    )
    link_extractor = WikipediaLinkExtractor()
    http_client = AsyncHttpClient(settings=settings)

    for page in settings.mediawiki_start_pages:
        page_links = await fetch_wiki_page_links(
            page=page,
            link_extractor=link_extractor,
            settings=settings,
            http_client=http_client,
        )

        contents = await asyncio.gather(
            *[
                download_page(
                    page_id=page_link.page_id,
                    settings=settings,
                    http_client=http_client,
                    storage_handler=storage_handler,
                )
                for page_link in page_links
                if isinstance(page_link, WikiPageLink)
            ]
        )

        for result in contents:
            if isinstance(result, Exception):
                logger.error(f"Error: {result}")

        logger.info(
            f"downloaded {len(contents)} contents for {page.page_id}",
        )

    logger.info("Flow completed successfully.")
