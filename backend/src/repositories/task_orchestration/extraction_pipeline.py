from typing import Literal

from prefect import flow, get_run_logger
from pydantic import HttpUrl

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.local_storage.html_storage import LocalTextStorage
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.repositories.search.meili_indexer import MeiliIndexer
from src.repositories.task_orchestration.flows.task_downloader import DownloaderFlow
from src.repositories.task_orchestration.flows.task_graph_storage import DBStorageFlow
from src.repositories.task_orchestration.flows.task_html_parsing import HtmlParsingFlow
from src.repositories.task_orchestration.flows.task_indexer import SearchIndexerFlow
from src.settings import Settings


@flow
def batch_extraction_flow(
    settings: Settings,
    entity: Literal["Movie", "Person"],
) -> None:
    """
    - extract films from Wikipedia
    - analyze their content
    - index them into a search engine
    - store results in a graph database.

    TODO:
    - rename flows by tasks (ex: HtmlParsingFlow -> HtmlParsingTask)
    """

    logger = get_run_logger()

    match entity:
        case "Movie":
            entity_type = Film
        case "Person":

            entity_type = Person
        case _:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    html_storage = LocalTextStorage(
        path=settings.persistence_directory,
        entity_type=entity_type,
    )

    json_storage = JSONEntityStorageHandler[entity_type](settings=settings)

    http_client = SyncHttpClient(settings=settings)

    # pages
    entity_pages = [
        p
        for p in settings.mediawiki_start_pages
        if p.toc_content_type == entity_type.__name__.lower()
    ]

    # make them unique by page_id
    entity_pages = {p.page_id: p for p in entity_pages}.values()

    download_flow = DownloaderFlow(settings=settings, http_client=http_client)

    analysis_flow = HtmlParsingFlow(
        settings=settings,
        entity_type=entity_type,
    )

    # for each page
    for config in entity_pages:
        content_ids = download_flow.execute(
            start_page=config,
            storage_handler=html_storage,
            return_results=True,  # return the list of page IDs
        )

        if not content_ids:
            logger.warning(f"No content found in page '{config.page_id}'")

        analysis_flow.execute(
            content_ids=content_ids,
            input_storage=html_storage,
            output_storage=json_storage,  # persist the parsed entity
        )

    if settings.meili_base_url:
        search_flow = SearchIndexerFlow(
            settings=settings,
            entity_type=entity_type,
        )

        # for all pages
        search_flow.execute(
            input_storage=json_storage,
            output_storage=MeiliIndexer[entity_type](settings=settings),
        )

    if settings.graph_db_uri:
        db_handler = (
            FilmGraphHandler(settings=settings)
            if entity_type is Film
            else PersonGraphHandler(settings=settings)
        )
        storage_flow = DBStorageFlow(
            settings=settings,
            entity_type=entity_type,
        )

        storage_flow.execute(
            input_storage=json_storage,
            output_storage=db_handler,
        )


@flow
def unit_extraction_flow(
    settings: Settings,
    entity: Literal["Movie", "Person"],
    permalink: HttpUrl,
) -> None:
    """
    Extract a single entity (Film or Person) from a given permalink.
    This flow will download the content, parse it, index it, and store it in the graph database.

    TODO:
    - unit indexation
    - unit storage
    - factorize the code with the batch extraction flow through a common flow `extraction_flow` taking various input parameters.
    """

    logger = get_run_logger()

    match entity:
        case "Movie":
            entity_type = Film
        case "Person":
            entity_type = Person
        case _:
            raise ValueError(f"Unsupported entity type: {entity}")

    page_id = str(permalink).split("/")[-1]  # Extract page ID from permalink

    html_storage = LocalTextStorage(
        path=settings.persistence_directory,
        entity_type=entity_type,
    )

    json_storage = JSONEntityStorageHandler[entity_type](settings=settings)

    http_client = SyncHttpClient(settings=settings)

    downloader_flow = DownloaderFlow(
        settings=settings,
        http_client=http_client,
    )

    analysis_flow = HtmlParsingFlow(
        settings=settings,
        entity_type=entity_type,
    )

    content_id = downloader_flow.download(
        page_id=page_id,
        storage_handler=html_storage,
        return_content=False,  # use the storage to persist the content
    )

    if content_id is None:
        logger.warning(f"No content found for page ID '{page_id}'")
        return

    analysis_flow.execute(
        content_ids=[content_id],
        input_storage=html_storage,
        output_storage=json_storage,  # persist the parsed entity
    )

    # # index the films into a search engine
    if settings.meili_base_url:
        search_flow = SearchIndexerFlow(
            settings=settings,
            entity_type=entity_type,
        )

        # for all pages
        search_flow.execute(
            input_storage=json_storage,
            output_storage=MeiliIndexer[entity_type](settings=settings),
        )

    if settings.graph_db_uri:
        db_handler = (
            FilmGraphHandler(settings=settings)
            if entity_type is Film
            else PersonGraphHandler(settings=settings)
        )
        storage_flow = DBStorageFlow(
            settings=settings,
            entity_type=entity_type,
        )
        storage_flow.execute(
            input_storage=json_storage,
            output_storage=db_handler,
        )
