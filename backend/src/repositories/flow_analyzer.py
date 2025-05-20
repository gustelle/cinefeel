import asyncio

from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from src.entities.film import Film
from src.entities.wiki import WikiPageLink
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.link_extractor import ILinkExtractor
from src.repositories.html_analyzer import HtmlContentAnalyzer
from src.repositories.html_storage import HtmlContentStorageHandler
from src.repositories.json_storage import JSONFilmStorageHandler
from src.settings import Settings, WikiTOCPageConfig

CONCURRENCY = 4


@task(cache_policy=NO_CACHE)
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

    logger = get_run_logger()
    try:

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

    except HttpError as e:
        if e.status_code == 404:
            logger.error(f"Page '{page_id}' not found")
        return None


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
def analyze_films(
    settings: Settings,
) -> None:

    logger = get_run_logger()

    html_storage = HtmlContentStorageHandler[Film](
        path=settings.persistence_directory,
    )

    film_storage = JSONFilmStorageHandler(settings=settings)

    analyzer = HtmlContentAnalyzer()

    i = 0

    # iterate over the list of films
    for html_content in html_storage.scan():
        # analyze the HTML content

        film = analyzer.analyze(html_content)

        if film is not None:
            # store the film entity
            film_storage.insert(film.uid, film.model_dump(mode="json"))

        i += 1
        if i > 2:
            break

    logger.info("Flow completed successfully.")
