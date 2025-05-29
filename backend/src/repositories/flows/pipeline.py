import asyncio

from prefect import flow, get_run_logger

from src.entities.content import PageLink
from src.entities.film import Film
from src.entities.person import Person
from src.repositories.flows.task_analyzer import AnalysisFlow
from src.repositories.flows.task_downloader import download_page, fetch_page_links
from src.repositories.flows.task_indexer import IndexerFlow
from src.repositories.html_parser.wikipedia_extractor import WikipediaExtractor
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

        local_film_storage = LocalTextStorage[self.entity_type](
            path=self.settings.persistence_directory,
        )

        link_extractor = WikipediaExtractor()
        http_client = AsyncHttpClient(settings=self.settings)

        # film pages
        film_pages = [
            p
            for p in self.settings.mediawiki_start_pages
            if p.toc_content_type == self.entity_type.__name__.lower()
        ]

        logger.info(
            f"Starting analysis for {len(film_pages)} pages of type {self.entity_type.__name__}."
        )

        for config in film_pages:

            page_links = await fetch_page_links(
                config=config,
                link_extractor=link_extractor,
                settings=self.settings,
                http_client=http_client,
            )

            film_ids = await asyncio.gather(
                *[
                    download_page(
                        page_id=page_link.page_id,
                        settings=self.settings,
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
            logger.info(f"IDs: {film_ids}")

            # filter the contents to only include the ones that are not already in the storage
            AnalysisFlow(
                settings=self.settings,
                entity_type=self.entity_type,
            ).execute(
                content_ids=film_ids,
                storage_handler=local_film_storage,
            )

        # finally, index the films
        # here we can iterate over all the films in the storage
        # indexing is not a blocking operation
        IndexerFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute()

        logger.info("Flow completed successfully.")
