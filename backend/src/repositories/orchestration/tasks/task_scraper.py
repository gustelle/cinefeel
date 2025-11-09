from __future__ import annotations

from logging import Logger

from prefect import runtime, task
from prefect.concurrency.sync import rate_limit

from src.entities.content import PageLink, TableOfContents
from src.exceptions import HttpError
from src.interfaces.http_client import IHttpClient
from src.interfaces.info_retriever import IContentParser
from src.interfaces.stats import IStatsCollector, StatKey
from src.interfaces.storage import IStorageHandler
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.repositories.wikipedia import download_page
from src.settings import ScrapingSettings

from .logger import get_logger


def download_and_store(
    http_client: IHttpClient,
    page_id: str,
    storage_handler: IStorageHandler,
    return_content: bool,
    scraping_settings: ScrapingSettings,
    stats_collector: IStatsCollector | None = None,
    flow_id: str | None = None,
) -> str | None:
    """
    Helper function to download a page and update stats.
    """

    try:

        rate_limit("api-rate-limiting", occupy=1)

        html = download_page(
            http_client=http_client,
            page_id=page_id,
            storage_handler=storage_handler,
            return_content=return_content,
            settings=scraping_settings,
        )

        if stats_collector:
            if html is not None:
                stats_collector.inc_value(StatKey.SCRAPING_SUCCESS, flow_id=flow_id)
            else:
                stats_collector.inc_value(StatKey.SCRAPING_VOID, flow_id=flow_id)

        if html is not None and storage_handler is not None:
            storage_handler.insert(
                content_id=page_id,
                content=html,
            )

        if return_content:
            return html

        return page_id if html is not None else None

    except HttpError as e:

        if e.status_code == 404:
            if stats_collector:
                stats_collector.inc_value(StatKey.SCRAPING_VOID, flow_id=flow_id)
            return None
        else:
            if stats_collector:
                stats_collector.inc_value(StatKey.SCRAPING_FAILED, flow_id=flow_id)
            # eventually retry or fail
            raise


def extract_page_links(
    http_client: IHttpClient,
    config: TableOfContents,
    link_extractor: IContentParser,
    scraping_settings: ScrapingSettings,
) -> list[PageLink]:
    """
    downloads the HTML page and extracts the links from it.

    Args:
        page (WikiTOCPageConfig): The configuration for the page to be downloaded.

    Returns:
        list[PageLink]: A list of page links.
    """

    logger: Logger = get_logger()

    rate_limit("api-rate-limiting", occupy=1)

    html = download_page(
        http_client=http_client,
        page_id=config.page_id,
        return_content=True,  # return the content
        settings=scraping_settings,
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

        logger.error(f"Error extracting links: {e}")
        return []


@task(
    task_run_name="execute_task-{page.page_id}",
    tags=["scraping"],  # mark as scraping task
)
def execute_task(
    page: PageLink,
    scraping_settings: ScrapingSettings,
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
        scraping_settings (ScrapingSettings): The scraping settings to use for the scraping process.
        http_client (IHttpClient): The HTTP client to use for making requests.

    Returns:
        list[str] | None: a list of `page_id` stored into the storage backend
            if `return_results` is set to True, else None
    """

    flow_id = runtime.flow_run.id

    if isinstance(page, TableOfContents):
        # extract the links from the table of contents
        page_links = extract_page_links(
            http_client=http_client,
            config=page,
            link_extractor=link_extractor,
            scraping_settings=scraping_settings,
        )
    else:
        page_links = [page]

    content_ids: set[str | None] = set()

    for page_link in page_links:
        if isinstance(page_link, PageLink):

            content_ids.add(
                download_and_store(
                    http_client=http_client,
                    page_id=page_link.page_id,
                    storage_handler=storage_handler,
                    return_content=False,  # for memory constraints, return the content ID
                    scraping_settings=scraping_settings,
                    stats_collector=stats_collector,
                    flow_id=flow_id,
                )
            )

    # filter out None values
    content_ids = {cid for cid in content_ids if cid is not None}

    if return_results:
        return list(content_ids)
