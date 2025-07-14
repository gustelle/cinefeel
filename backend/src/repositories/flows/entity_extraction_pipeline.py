from prefect import flow, get_run_logger

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.pipeline import IPipelineRunner
from src.repositories.flows.tasks.task_downloader import DownloaderFlow
from src.repositories.flows.tasks.task_html_parsing import HtmlParsingFlow
from src.repositories.flows.tasks.task_indexer import IndexerFlow
from src.repositories.http.async_http import AsyncHttpClient
from src.repositories.local_storage.html_storage import LocalTextStorage
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.repositories.search.meili_indexer import MeiliIndexer
from src.settings import Settings


class Html2EntitiesPipeline(IPipelineRunner):
    """
    Scrape Wikipedia pages for a specific entity type (Film or Person),
    analyze the content, index it into a search engine, and store results in a graph database
    """

    entity_type: type[Film | Person]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Film | Person]):
        self.entity_type = entity_type
        self.settings = settings

    @flow(
        name="Wikipedia Analysis Flow",
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

        meili_storage = MeiliIndexer[self.entity_type](settings=self.settings)

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
        # here we can iterate over all the films in the storage
        # indexing is not a blocking operation
        IndexerFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute(
            input_storage=json_storage,
            output_storage=meili_storage,
        )

        logger.info("Flow completed successfully.")
