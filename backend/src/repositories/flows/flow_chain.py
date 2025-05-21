import asyncio

from prefect import flow, get_run_logger

from src.entities.film import Film
from src.entities.wiki import WikiPageLink
from src.repositories.html_parser.wikipedia_extractor import WikipediaLinkExtractor
from src.repositories.http.async_http import AsyncHttpClient
from src.repositories.storage.html_storage import HtmlContentStorageHandler
from src.settings import Settings

from .task_analyzer import analyze_films
from .task_downloader import download_page, fetch_wiki_page_links
from .task_indexer import index_films


@flow()
async def run_chain(
    settings: Settings,
) -> None:

    logger = get_run_logger()

    storage_handler = HtmlContentStorageHandler[Film](
        path=settings.persistence_directory,
    )
    link_extractor = WikipediaLinkExtractor()
    http_client = AsyncHttpClient(settings=settings)

    for page in settings.mediawiki_start_pages:

        logger.info(f"Processing page: {page.page_id}")

        page_links = await fetch_wiki_page_links(
            page=page,
            link_extractor=link_extractor,
            settings=settings,
            http_client=http_client,
        )

        # TODO: contents should be a list of Film entities
        # to pass to the analyzer
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

        # TODO: pass the contents to the analyzer
        analyze_films(
            settings=settings,
        )

        # TODO: pass the contents to the indexer
        index_films(
            settings=settings,
        )

    logger.info("Flow completed successfully.")
