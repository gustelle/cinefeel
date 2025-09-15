from prefect import flow, get_run_logger

from src.entities.content import TableOfContents
from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.orchestration.tasks.task_downloader import PageContentDownloader
from src.settings import Settings


@flow(
    name="scrape_flow",
    description="Scrapes Wikipedia pages and stores them into a storage backend.",
)
def scraping_flow(
    settings: Settings,
    pages: list[TableOfContents],
) -> None:

    logger = get_run_logger()

    http_client = SyncHttpClient(settings=settings)

    download_flow = PageContentDownloader(settings=settings, http_client=http_client)

    # make them unique by page_id
    pages = {p.page_id: p for p in pages}.values()

    # for each page
    for config in pages:

        logger.info(
            f"Processing '{config.__class__.__name__}' with ID '{config.page_id}'"
        )

        match config.entity_type:
            case "Movie":
                entity_type = Film
            case "Person":
                entity_type = Person
            case _:
                raise ValueError(f"Unsupported entity type: {entity_type}")

        html_store = RedisTextStorage(settings=settings)

        download_flow.execute.submit(
            page=config,
            storage_handler=html_store,
            return_results=False,
        )
