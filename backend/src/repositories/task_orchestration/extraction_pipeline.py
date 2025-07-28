from prefect import flow, get_run_logger
from pydantic import HttpUrl

from src.entities.composable import Composable
from src.entities.film import Film
from src.interfaces.http_client import IHttpClient
from src.interfaces.pipeline import IPipelineRunner
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.http.async_http import AsyncHttpClient
from src.repositories.local_storage.html_storage import LocalTextStorage
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.repositories.search.meili_indexer import MeiliIndexer
from src.repositories.task_orchestration.flows.task_downloader import DownloaderFlow
from src.repositories.task_orchestration.flows.task_graph_storage import DBStorageFlow
from src.repositories.task_orchestration.flows.task_html_parsing import HtmlParsingFlow
from src.repositories.task_orchestration.flows.task_indexer import SearchIndexerFlow
from src.settings import Settings


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

    @flow(
        name="Batch Wikipedia Extraction Pipeline",
    )
    async def execute_pipeline(
        self,
    ) -> None:

        logger = get_run_logger()

        html_storage = LocalTextStorage(
            path=self.settings.persistence_directory,
            entity_type=self.entity_type,
        )

        json_storage = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        http_client = AsyncHttpClient(settings=self.settings)

        # pages
        entity_pages = [
            p
            for p in self.settings.mediawiki_start_pages
            if p.toc_content_type == self.entity_type.__name__.lower()
        ]

        # make them unique by page_id
        entity_pages = {p.page_id: p for p in entity_pages}.values()

        downloader_flow = DownloaderFlow(
            settings=self.settings,
            http_client=http_client,
        )

        analysis_flow = HtmlParsingFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        )

        for config in entity_pages:

            content_ids = await downloader_flow.execute(
                start_page=config,
                storage_handler=html_storage,
                return_results=True,  # return the list of page IDs
            )

            # filter the contents to only include the ones that are not already in the storage
            analysis_flow.execute(
                content_ids=content_ids,
                input_storage=html_storage,
                output_storage=json_storage,
            )

        # index the films into a search engine
        SearchIndexerFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute(
            input_storage=json_storage,
            output_storage=MeiliIndexer[self.entity_type](settings=self.settings),
        )

        # Store in the graph database
        db_storage = (
            FilmGraphHandler(settings=self.settings)
            if self.entity_type is Film
            else PersonGraphHandler(settings=self.settings)
        )
        DBStorageFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute(input_storage=json_storage, output_storage=db_storage)

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

        logger = get_run_logger()

        page_id = str(permalink).split("/")[-1]  # Extract page ID from permalink

        html_storage = LocalTextStorage(
            path=self.settings.persistence_directory,
            entity_type=self.entity_type,
        )

        json_storage = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        downloader_flow = DownloaderFlow(
            settings=self.settings,
            http_client=self.http_client,
        )

        content_id = downloader_flow.download(
            page_id=page_id,
            storage_handler=html_storage,
            return_content=False,  # use the storage to persist the content
        )

        HtmlParsingFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute(
            content_ids=[content_id],
            input_storage=html_storage,
            output_storage=json_storage,  # persist the parsed entity
        ).deploy(
            name="html-parsing",
            work_pool_name="local-processes",
        )

        logger.info("Deployed HTML parsing flow.")

        # index the films into a search engine
        if self.settings.meili_base_url:
            SearchIndexerFlow(
                settings=self.settings,
                entity_type=self.entity_type,
            ).execute(
                input_storage=json_storage,
                output_storage=MeiliIndexer[self.entity_type](settings=self.settings),
            ).deploy(
                name="meili-indexing",
                work_pool_name="local-processes",
            )

            logger.info("Deployed Meili search indexing flow.")
        else:
            logger.warning("Meili base URL is not set. Skipping search indexing step.")

        # Store in the graph database
        if self.settings.graph_db_uri:
            db_storage = (
                FilmGraphHandler(settings=self.settings)
                if self.entity_type is Film
                else PersonGraphHandler(settings=self.settings)
            )
            DBStorageFlow(
                settings=self.settings,
                entity_type=self.entity_type,
            ).execute(input_storage=json_storage, output_storage=db_storage).deploy(
                name="db-storage",
                work_pool_name="local-processes",
            )

            logger.info("Deployed graph database storage flow.")
        else:
            logger.warning(
                "Graph database URI is not set. Skipping graph storage step."
            )
