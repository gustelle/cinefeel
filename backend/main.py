import time

import typer
import uvloop
from loguru import logger

from src.entities.film import Film
from src.entities.person import Person

app = typer.Typer()


@app.command(
    help="Download the HTML content from Wikipedia pages and store it in a local directory."
)
def crawl():
    uvloop.run(async_crawl())


@app.command()
def extract():

    from src.repositories.html_analyzer import HtmlContentAnalyzer
    from src.repositories.html_storage import HtmlContentStorageHandler
    from src.repositories.json_storage import (
        JSONFilmStorageHandler,
        JSONPersonStorageHandler,
    )
    from src.settings import Settings
    from src.use_cases.extract_uc import HtmlExtractionUseCase

    settings = Settings()

    uc = HtmlExtractionUseCase(
        storage_handler=JSONFilmStorageHandler(settings=settings),
        html_retriever=HtmlContentStorageHandler[Film](
            path=settings.persistence_directory
        ),
        html_extractor=HtmlContentAnalyzer(),
        settings=settings,
    )
    uc.execute(wait_for_completion=True)

    logger.info("Extraction of films completed.")

    uc = HtmlExtractionUseCase(
        storage_handler=JSONPersonStorageHandler(settings=settings),
        html_retriever=HtmlContentStorageHandler[Person](
            path=settings.persistence_directory
        ),
        html_extractor=HtmlContentAnalyzer(),
        settings=settings,
    )
    uc.execute(wait_for_completion=True)

    logger.info("Extraction of persons completed.")


@app.command()
def index():

    from src.entities.film import Film
    from src.entities.person import Person
    from src.repositories.json_storage import (
        JSONFilmStorageHandler,
        JSONPersonStorageHandler,
    )
    from src.repositories.meili_indexer import MeiliIndexer
    from src.settings import Settings
    from src.use_cases.index_uc import IndexerUseCase

    settings = Settings()
    film_storage_handler = JSONFilmStorageHandler(settings=settings)
    person_storage_handler = JSONPersonStorageHandler(settings=settings)

    uc = IndexerUseCase(
        indexer=MeiliIndexer[Film](settings=settings),
        storage_handler=film_storage_handler,
    )
    uc.execute(
        wait_for_completion=False,  # don't wait for the task to complete; return immediately
    )
    logger.info("Indexation of Films completed.")

    uc = IndexerUseCase(
        indexer=MeiliIndexer[Person](settings=settings),
        storage_handler=person_storage_handler,
    )
    uc.execute(
        wait_for_completion=False,  # don't wait for the task to complete; return immediately
    )

    logger.info("Indexation of Persons completed.")


async def async_crawl():

    from src.repositories.html_storage import HtmlContentStorageHandler
    from src.settings import Settings
    from src.use_cases.crawl_uc import WikipediaCrawlUseCase

    start_time = time.time()
    logger.info("Starting scraping...")

    settings = Settings()
    person_storage_handler = HtmlContentStorageHandler[Person](
        path=settings.persistence_directory
    )
    film_storage_handler = HtmlContentStorageHandler[Film](
        path=settings.persistence_directory
    )

    crawl = WikipediaCrawlUseCase(
        settings=settings,
        storage_handlers=[film_storage_handler, person_storage_handler],
    )

    await crawl.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info("Scraping completed in %.2f seconds." % elapsed_time)


if __name__ == "__main__":

    app()
