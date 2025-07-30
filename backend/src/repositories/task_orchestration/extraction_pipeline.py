from typing import Literal

from loguru import logger
from prefect import flow, get_run_logger  # , get_run_logger
from pydantic import HttpUrl

from src.entities.composable import Composable
from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.http_client import IHttpClient
from src.interfaces.pipeline import IPipelineRunner
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
def extraction_flow(
    settings: Settings,  # http_client: IHttpClient, storage_handler: IStorageHandler
    entity: Literal["Movie", "Person"],
) -> None:
    """
    - extract films from Wikipedia
    - analyze their content
    - index them into a search engine
    - store results in a graph database.
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

    # http_client = AsyncHttpClient(settings=self.settings)
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

    search_flow = SearchIndexerFlow(
        settings=settings,
        entity_type=entity_type,
    )

    db_handler = (
        FilmGraphHandler(settings=settings)
        if entity_type is Film
        else PersonGraphHandler(settings=settings)
    )
    storage_flow = DBStorageFlow(
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

        if content_ids:
            logger.info(f"Downloaded {len(content_ids)} pages for {config.page_id}")
        else:
            logger.warning(f"No content downloaded for {config.page_id}")

        analysis_flow.execute(
            content_ids=content_ids,
            input_storage=html_storage,
            output_storage=json_storage,  # persist the parsed entity
        )

    # for all pages
    search_flow.execute(
        input_storage=json_storage,
        output_storage=MeiliIndexer[entity_type](settings=settings),
    )

    storage_flow.execute(
        input_storage=json_storage,
        output_storage=db_handler,
    )


class BatchExtractionPipeline(IPipelineRunner):
    """
    Scrape Wikipedia pages for a specific entity type (Film or Person),
    analyze the content, index it into a search engine, and store results in a graph database
    """

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Composable]):
        self.entity_type = entity_type
        self.settings = settings

    def execute_pipeline(
        self,
    ) -> None:

        pass

        # logger = get_run_logger()

        # html_storage = LocalTextStorage(
        #     path=self.settings.persistence_directory,
        #     entity_type=self.entity_type,
        # )

        # # json_storage = JSONEntityStorageHandler[self.entity_type](
        # #     settings=self.settings
        # # )

        # # http_client = AsyncHttpClient(settings=self.settings)
        # http_client = SyncHttpClient(settings=self.settings)

        # extraction_flow.serve(
        #     name="download-html-pages",
        #     parameters={
        #         "settings": self.settings,
        #         # "http_client": http_client,
        #         # "storage_handler": html_storage,
        #     },
        # )

        # # pages
        # entity_pages = [
        #     p
        #     for p in self.settings.mediawiki_start_pages
        #     if p.toc_content_type == self.entity_type.__name__.lower()
        # ]

        # # make them unique by page_id
        # entity_pages = {p.page_id: p for p in entity_pages}.values()

        # downloader_flow = DownloaderFlow(
        #     settings=self.settings,
        #     http_client=http_client,
        # )

        # analysis_flow = HtmlParsingFlow(
        #     settings=self.settings,
        #     entity_type=self.entity_type,
        # )

        #  for config in entity_pages:

        # content_ids = process_flow.serve(
        #     name="download-html-pages",
        #     parameters={
        #         "task_executor": downloader_flow,
        #         "start_page": config,
        #         "storage_handler": html_storage,
        #         "return_results": True,  # return the list of page IDs
        #     },
        # )

        # filter the contents to only include the ones that are not already in the storage
        # analysis_flow.execute.serve(
        #     name="html-parsing",
        #     parameters={
        #         "content_ids": content_ids,
        #         "input_storage": html_storage,
        #         "output_storage": json_storage,  # persist the parsed entity
        #     },
        # )

        # index the films into a search engine
        # SearchIndexerFlow(
        #     settings=self.settings,
        #     entity_type=self.entity_type,
        # ).execute.serve(
        #     name="meili-indexing",
        #     parameters={
        #         "input_storage": json_storage,
        #         "output_storage": MeiliIndexer[self.entity_type](
        #             settings=self.settings
        #         ),
        #     },
        # )

        # Store in the graph database
        # db_storage = (
        #     FilmGraphHandler(settings=self.settings)
        #     if self.entity_type is Film
        #     else PersonGraphHandler(settings=self.settings)
        # )
        # DBStorageFlow(
        #     settings=self.settings,
        #     entity_type=self.entity_type,
        # ).execute.serve(
        #     name="db-storage",
        #     parameters={
        #         "input_storage": json_storage,
        #         "output_storage": db_storage,
        #     },
        # )

        logger.info("Flow completed successfully.")


class UnitExtractionPipeline(IPipelineRunner):
    """
    Scrape a single page for a specific entity type (Film or Person),
    analyze the content, index it into a search engine, and store results in a graph database
    """

    entity_type: type[Composable]
    settings: Settings
    http_client: IHttpClient

    def __init__(
        self,
        settings: Settings,
        entity_type: type[Composable],
        http_client: IHttpClient,
    ):
        self.entity_type = entity_type
        self.settings = settings
        self.http_client = http_client

    @flow(
        name="Unit extraction pipeline",
    )
    def execute_pipeline(
        self,
        permalink: HttpUrl,
    ) -> None:
        pass

        # logger = get_run_logger()

        # page_id = str(permalink).split("/")[-1]  # Extract page ID from permalink

        # html_storage = LocalTextStorage(
        #     path=self.settings.persistence_directory,
        #     entity_type=self.entity_type,
        # )

        # json_storage = JSONEntityStorageHandler[self.entity_type](
        #     settings=self.settings
        # )

        # downloader_flow = DownloaderFlow(
        #     settings=self.settings,
        #     http_client=self.http_client,
        # )

        # content_id = downloader_flow.download(
        #     page_id=page_id,
        #     storage_handler=html_storage,
        #     return_content=False,  # use the storage to persist the content
        # )

        # HtmlParsingFlow(
        #     settings=self.settings,
        #     entity_type=self.entity_type,
        # ).execute.serve(
        #     name="html-parsing",
        #     parameters={
        #         "content_ids": [content_id],
        #         "input_storage": html_storage,
        #         "output_storage": json_storage,  # persist the parsed entity
        #     },
        # )

        # logger.info("Deployed HTML parsing flow.")

        # # index the films into a search engine
        # if self.settings.meili_base_url:
        #     SearchIndexerFlow(
        #         settings=self.settings,
        #         entity_type=self.entity_type,
        #     ).execute.serve(
        #         name="meili-indexing",
        #         parameters={
        #             "input_storage": json_storage,
        #             "output_storage": MeiliIndexer[self.entity_type](
        #                 settings=self.settings
        #             ),
        #         },
        #     )

        #     logger.info("Deployed Meili search indexing flow.")
        # else:
        #     logger.warning("Meili base URL is not set. Skipping search indexing step.")

        # # Store in the graph database
        # if self.settings.graph_db_uri:
        #     db_storage = (
        #         FilmGraphHandler(settings=self.settings)
        #         if self.entity_type is Film
        #         else PersonGraphHandler(settings=self.settings)
        #     )
        #     DBStorageFlow(
        #         settings=self.settings,
        #         entity_type=self.entity_type,
        #     ).execute.serve(
        #         name="db-storage",
        #         parameters={
        #             "input_storage": json_storage,
        #             "output_storage": db_storage,
        #         },
        #     )

        #     logger.info("Deployed graph database storage flow.")
        # else:
        #     logger.warning(
        #         "Graph database URI is not set. Skipping graph storage step."
        #     )
