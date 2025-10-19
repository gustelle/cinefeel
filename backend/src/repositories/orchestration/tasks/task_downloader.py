from __future__ import annotations

import orjson
from loguru import logger
from prefect import get_run_logger, runtime, task

from src.entities.content import PageLink, TableOfContents
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.info_retriever import IContentParser
from src.interfaces.stats import IStatsCollector, StatKey
from src.interfaces.storage import IStorageHandler
from src.repositories.db.local_storage.html_storage import LocalTextStorage
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.settings import Settings


def download(
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
        str | None: The content ID if the download was successful, None otherwise.
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


def extract_page_links(
    http_client: IHttpClient,
    config: TableOfContents,
    link_extractor: IContentParser,
    settings: Settings,
) -> list[PageLink]:
    """
    downloads the HTML page and extracts the links from it.

    Args:
        page (WikiTOCPageConfig): The configuration for the page to be downloaded.

    Returns:
        list[PageLink]: A list of page links.
    """

    logger = get_run_logger()

    html = download(
        http_client=http_client,
        page_id=config.page_id,
        return_content=True,  # return the content
        settings=settings,
    )

    if html is None:
        return []

    try:

        _links = link_extractor.retrieve_inner_links(
            html_content=html,
            config=config,
        )

        return _links

    except Exception as e:
        logger.error(f"Error extracting list of movies: {e}")
        return []


@task(
    task_run_name="execute_task-{page.page_id}",
    tags=["scraping"],  # mark as scraping task
)
def execute_task(
    page: PageLink,
    settings: Settings,
    http_client: IHttpClient,
    storage_handler: IStorageHandler,
    link_extractor: IContentParser | None = WikipediaParser(),
    return_results: bool = False,
    stats_collector: IStatsCollector | None = None,
) -> list[str] | None:
    """
    Entry point to scrape a page and store its HTML content. This function
    runs the task to download the HTML content of a page and store it using the provided storage handler.
    - If the `page` is a `TableOfContents`, it will first extract the links from the table of contents
    and then download each linked page.
    - If the `page` is a `PageLink`, it will directly download the page.

    Args:
        page (PageLink): The permalink to the page to be downloaded.
        storage_handler (IStorageHandler): the storage handler to use for storing the content that is downloaded.
        link_extractor (IContentParser | None, optional): The link extractor to use for extracting links from a table of contents.
            Defaults to `WikipediaParser`.
        return_results (bool, optional): Defaults to False.
            If True, the method will return a list of `page_id` stored into the storage backend.
            If False, it will return None.
        stats_collector (IStatsCollector | None): The stats collector to use for collecting statistics during the scraping process.
            Defaults to None.

    Returns:
        list[str] | None: a list of `page_id` stored into the storage backend
            if `return_results` is set to True, else None
    """

    if isinstance(page, TableOfContents):
        # extract the links from the table of contents
        page_links = extract_page_links(
            http_client=http_client,
            config=page,
            link_extractor=link_extractor,
            settings=settings,
        )
    else:
        page_links = [page]

    content_ids = [
        download(
            http_client=http_client,
            page_id=page_link.page_id,
            storage_handler=storage_handler,
            return_content=False,  # for memory constraints, return the content ID
            settings=settings,
            stats_collector=stats_collector,
        )
        for page_link in page_links
        if isinstance(page_link, PageLink)
    ]

    # filter out None values
    content_ids = [cid for cid in content_ids if cid is not None]

    if return_results:
        return content_ids
