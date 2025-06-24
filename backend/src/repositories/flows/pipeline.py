from prefect import flow, get_run_logger

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.flows.task_analyzer import AnalysisFlow
from src.repositories.flows.task_downloader import DownloaderFlow
from src.repositories.flows.task_indexer import IndexerFlow
from src.repositories.http.async_http import AsyncHttpClient
from src.repositories.storage.html_storage import LocalTextStorage
from src.settings import Settings


class PipelineRunner:

    entity_type: type[Film | Person]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Film | Person]):
        self.entity_type = entity_type
        self.settings = settings

    @flow(
        name="Wikipedia Analysis Flow",
    )
    async def run_chain(
        self,
    ) -> None:

        logger = get_run_logger()

        html_storage = LocalTextStorage[self.entity_type](
            path=self.settings.persistence_directory,
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

        logger.info(
            f"Found {len(entity_pages)} pages of type {self.entity_type.__name__} in the settings."
        )

        downloader_flow = DownloaderFlow(
            settings=self.settings,
            http_client=http_client,
        )

        analysis_flow = AnalysisFlow(
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
                storage_handler=html_storage,
            )

        # finally, index the films
        # here we can iterate over all the films in the storage
        # indexing is not a blocking operation
        IndexerFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute()

        logger.info("Flow completed successfully.")
