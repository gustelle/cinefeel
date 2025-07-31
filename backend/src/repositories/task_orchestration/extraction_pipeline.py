from typing import Literal

from prefect import flow, get_run_logger
from pydantic import HttpUrl

from src.entities.content import PageLink
from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.local_storage.html_storage import LocalTextStorage
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.repositories.search.meili_indexer import MeiliHandler
from src.repositories.task_orchestration.flows.task_downloader import (
    PageContentDownloader,
)
from src.repositories.task_orchestration.flows.task_graph_storage import (
    DBStorageUpdater,
)
from src.repositories.task_orchestration.flows.task_html_parsing import (
    HtmlEntityExtractor,
)
from src.repositories.task_orchestration.flows.task_indexer import SearchUpdater
from src.settings import Settings


@flow
def batch_extraction_flow(
    settings: Settings,
    page_links: list[PageLink],
) -> None:
    """
    - extract films from Wikipedia
    - analyze their content
    - index them into a search engine
    - store results in a graph database.


    Args:
        settings (Settings): The application settings.
        page_links (list[PageLink]): The list of page links to extract.
    """

    logger = get_run_logger()

    http_client = SyncHttpClient(settings=settings)

    download_flow = PageContentDownloader(settings=settings, http_client=http_client)

    # make them unique by page_id
    page_links = {p.page_id: p for p in page_links}.values()

    # for each page
    for config in page_links:

        match config.entity_type:
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

        analysis_flow = HtmlEntityExtractor(
            settings=settings,
            entity_type=entity_type,
        )

        json_storage = JSONEntityStorageHandler[entity_type](settings=settings)

        content_ids = download_flow.execute(
            page=config,
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
        search_flow = SearchUpdater(
            settings=settings,
            entity_type=entity_type,
        )

        # for all pages
        search_flow.execute(
            input_storage=json_storage,
            output_storage=MeiliHandler[entity_type](settings=settings),
        )

    if settings.graph_db_uri:
        db_handler = (
            FilmGraphHandler(settings=settings)
            if entity_type is Film
            else PersonGraphHandler(settings=settings)
        )
        storage_flow = DBStorageUpdater(
            settings=settings,
            entity_type=entity_type,
        )

        storage_flow.execute(
            input_storage=json_storage,
            output_storage=db_handler,
        )


@flow(
    name="Unit Extraction Flow",
    description="Extract a single entity (Film or Person) from a given permalink.",
)
def unit_extraction_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
    permalink: HttpUrl,
) -> None:
    """
    Extract a single entity (Film or Person) from a given permalink.
    This flow will download the content, parse it, index it, and store it in the graph database.
    """

    page_id = str(permalink).split("/")[-1]  # Extract page ID from permalink

    page_link = PageLink(
        page_title=None,  # Title is not used in this flow
        page_id=page_id,
        entity_type=entity_type,
    )

    batch_extraction_flow(
        settings=settings,
        page_links=[page_link],  # Wrap in a list to match the expected type
    )
