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
def download():
    uvloop.run(async_download())


@app.command()
def extract():

    from src.repositories.html_analyzer import HtmlContentAnalyzer
    from src.repositories.html_storage import HtmlContentStorageHandler
    from src.repositories.json_storage import (
        JSONFilmStorageHandler,
        JSONPersonStorageHandler,
    )
    from src.settings import Settings
    from src.use_cases.extract_uc import JsonExtractionUseCase

    settings = Settings()

    # where the JSON files are extracted
    film_storage_handler = JSONFilmStorageHandler(settings=settings)
    person_strorage_handler = JSONPersonStorageHandler(settings=settings)

    # where the raw html is stored
    html_person_retriever = HtmlContentStorageHandler[Person](
        path=settings.persistence_directory
    )
    html_film_retriever = HtmlContentStorageHandler[Film](
        path=settings.persistence_directory
    )

    analyzer = HtmlContentAnalyzer()

    # TODO: Split in 2 steps:
    # 1. extract Persons
    # 2. extract Films
    # instead of using the same use case for both which makes it more complex
    uc = JsonExtractionUseCase(
        storage_handlers=[film_storage_handler, person_strorage_handler],
        html_retrievers=[
            html_person_retriever,
            html_film_retriever,
        ],  # where raw html can be found
        html_extractor=analyzer,
        settings=settings,
    )
    uc.execute(wait_for_completion=True)

    logger.info("Extraction of films completed.")

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


async def async_download():

    from src.repositories.html_storage import HtmlContentStorageHandler
    from src.settings import Settings
    from src.use_cases.scrape_uc import WikipediaDownloadUseCase

    start_time = time.time()
    logger.info("Starting scraping...")

    settings = Settings()
    person_storage_handler = HtmlContentStorageHandler[Person](
        path=settings.persistence_directory
    )
    film_storage_handler = HtmlContentStorageHandler[Film](
        path=settings.persistence_directory
    )

    scraping_use_case = WikipediaDownloadUseCase(
        settings=settings,
        storage_handlers=[film_storage_handler, person_storage_handler],
    )

    await scraping_use_case.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info("Scraping completed in %.2f seconds." % elapsed_time)


if __name__ == "__main__":

    app()
