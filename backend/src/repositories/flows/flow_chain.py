import asyncio

from prefect import flow, get_run_logger

from src.entities.content import PageLink
from src.entities.film import Film
from src.entities.person import Person
from src.repositories.flows.task_analyzer import analyze_films, analyze_persons
from src.repositories.flows.task_downloader import download_page, fetch_page_links
from src.repositories.flows.task_indexer import index_films, index_persons
from src.repositories.html_parser.wikipedia_extractor import WikipediaExtractor
from src.repositories.http.async_http import AsyncHttpClient
from src.repositories.storage.html_storage import LocalTextStorage
from src.settings import Settings


@flow()
async def run_chain(
    settings: Settings,
) -> None:

    logger = get_run_logger()

    local_film_storage = LocalTextStorage[Film](
        path=settings.persistence_directory,
    )
    local_person_storage = LocalTextStorage[Person](
        path=settings.persistence_directory,
    )
    link_extractor = WikipediaExtractor()
    http_client = AsyncHttpClient(settings=settings)

    # film pages
    film_pages = [
        p for p in settings.mediawiki_start_pages if p.toc_content_type == "film"
    ]

    person_pages = [
        p for p in settings.mediawiki_start_pages if p.toc_content_type == "person"
    ]

    for config in film_pages:

        page_links = await fetch_page_links(
            config=config,
            link_extractor=link_extractor,
            settings=settings,
            http_client=http_client,
        )

        film_ids = await asyncio.gather(
            *[
                download_page(
                    page_id=page_link.page_id,
                    settings=settings,
                    http_client=http_client,
                    storage_handler=local_film_storage,
                    return_content=False,  # for memory constraints, return the content ID
                )
                for page_link in page_links
                if isinstance(page_link, PageLink)
            ],
            return_exceptions=True,
        )

        film_ids = [cid for cid in film_ids if isinstance(cid, str)]

        logger.info(
            f"Downloaded {len(film_ids)} contents for {config.page_id}",
        )
        logger.info(f"Film IDs: {film_ids}")

        # filter the contents to only include the ones that are not already in the storage
        analyze_films(
            settings=settings,
            content_ids=film_ids,
        )

    # finally, index the films
    # here we can iterate over all the films in the storage
    # indexing is not a blocking operation
    index_films(
        settings=settings,
    )

    # logger.info("Films indexed successfully.")
    logger.info("Starting to download person pages...")

    for config in person_pages:

        page_links = await fetch_page_links(
            config=config,
            link_extractor=link_extractor,
            settings=settings,
            http_client=http_client,
        )

        person_ids = await asyncio.gather(
            *[
                download_page(
                    page_id=page_link.page_id,
                    settings=settings,
                    http_client=http_client,
                    storage_handler=local_person_storage,
                    return_content=False,  # for memory constraints, return the content ID
                )
                for page_link in page_links
                if isinstance(page_link, PageLink)
            ],
            return_exceptions=True,
        )

        person_ids = [cid for cid in person_ids if isinstance(cid, str)]

        logger.info(
            f"Downloaded {len(person_ids)} contents for {config.page_id}",
        )
        logger.info(f"Person IDs: {person_ids}")

        analyze_persons(
            settings=settings,
            content_ids=person_ids,
        )

    index_persons(
        settings=settings,
    )

    logger.info("Persons indexed successfully.")

    logger.info("Flow completed successfully.")
