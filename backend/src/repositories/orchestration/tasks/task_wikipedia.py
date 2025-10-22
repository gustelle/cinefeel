from __future__ import annotations

import orjson
from loguru import logger
from prefect import get_run_logger, runtime, task
from pydantic import HttpUrl

from src.exceptions import HttpError, RetrievalError
from src.interfaces.http_client import IHttpClient
from src.interfaces.stats import IStatsCollector, StatKey
from src.repositories.db.local_storage.html_storage import LocalTextStorage
from src.settings import Settings


@task(
    task_run_name="download_page-{page_id}",
    tags=["scraping"],  # mark as scraping task
)
def download_page(
    http_client: IHttpClient,
    page_id: str,
    settings: Settings,
    storage_handler: LocalTextStorage | None = None,
    return_content: bool = False,
    stats_collector: IStatsCollector | None = None,
    **params,
) -> str | None:
    """
    Pre-requisite: The class `http_client` provided must be synchronous (async not supported yet).

    Args:
        page_id (str): The page ID to download.
        storage_handler (LocalTextStorage | None, optional): The storage handler to use for storing the content. Defaults to None.
        return_content (bool, optional): Whether to return the content. Defaults to False, in which case the content ID is returned.
        stats_collector (IStatsCollector | None): The stats collector to use for collecting statistics during the scraping process.
            Defaults to None.
        **params: Additional parameters for the HTTP request.

    Returns:
        str | None:
            - If `return_content` is True, returns the HTML content as a string, or None if download failed.
            - If `return_content` is False, returns the page ID if download succeeded and content was stored, or None if download failed.
    """

    endpoint = f"{settings.mediawiki_base_url}/page/{page_id}/html"

    logger.info(f">> Downloading '{endpoint}'")

    flow_id = runtime.flow_run.id

    try:
        html = http_client.send(
            url=endpoint,
            response_type="text",
            params=params,
        )
    except HttpError as e:

        if stats_collector:
            stats_collector.inc_value(StatKey.SCRAPING_FAILED, flow_id=flow_id)

        if e.status_code == 404:
            logger.warning(
                f"Page '{page_id}' not found at '{endpoint}'. Skipping download."
            )
            if stats_collector:
                stats_collector.inc_value(StatKey.SCRAPING_VOID, flow_id=flow_id)
            return None
        else:
            # force a retry for other HTTP errors
            raise

    if html is not None and storage_handler is not None:
        storage_handler.insert(
            content_id=page_id,
            content=html,
        )

    if stats_collector:

        if html is not None:
            stats_collector.inc_value(StatKey.SCRAPING_SUCCESS, flow_id=flow_id)
        else:
            stats_collector.inc_value(StatKey.SCRAPING_VOID, flow_id=flow_id)

        logger.info(
            orjson.dumps(
                stats_collector.collect(flow_id=flow_id), option=orjson.OPT_INDENT_2
            ).decode()
        )

    if return_content:
        return html

    return page_id if html is not None else None


@task(
    task_run_name="get_permalink-{name}",
    tags=["scraping"],  # mark as scraping task
)
def get_permalink(name: str, http_client: IHttpClient) -> HttpUrl | None:
    """
    retrieves the permalink for a given Wikipedia page name.

    TODO:
    - test this function

    Example:
        >>> get_permalink("Some Wikipedia Page", http_client=http_client)
        # would be:
        # HttpUrl("https://fr.wikipedia.org/wiki/Some_Wikipedia_Page")

        >>> get_permalink("NonExistingPage", http_client=http_client)
        # would raise RetrievalError(...)

    Args:
        name (str): The name of the page to verify.

    Returns:
        str | None: the page ID of the page on Wikipedia, or None if not found.

    Raises:
        RetrievalError
    """

    try:

        logger = get_run_logger()

        if name is None or name.strip() == "":
            logger.warning(f"Invalid name provided: '{name}'")
            return None

        endpoint = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"
        response = http_client.send(
            url=endpoint,
            response_type="json",
        )
        page_id = response["key"]
        return HttpUrl(f"https://fr.wikipedia.org/wiki/{page_id}")

    except KeyError as e:
        raise RetrievalError(
            reason=f"Unexpected response structure when retrieving page ID for name '{name}': {str(e)}",
            status_code=500,
        ) from e
    except HttpError as e:
        raise RetrievalError(
            reason=f"HTTP error occurred while retrieving page ID for name '{name}': {e.reason}",
            status_code=e.status_code,
        ) from e
    except Exception as e:
        raise RetrievalError(
            reason=f"Unexpected error occurred while retrieving page ID for name '{name}': {str(e)}",
            status_code=500,
        ) from e


def get_page_id(permalink: HttpUrl) -> str:
    """Query wikipedia to get the page ID from a permalink.

    TODO:
    - test this function

    Args:
        permalink (HttpUrl): The permalink URL of the Wikipedia page.

    Returns:
        str: The extracted page ID.
    """
    try:
        # extract the page ID from the permalink
        return str(permalink).split("/wiki/")[-1]
    except Exception as e:
        raise RetrievalError(
            reason=f"Error extracting page ID from permalink '{permalink}': {str(e)}",
            status_code=500,
        ) from e
