import time

import typer
import uvloop

app = typer.Typer()


@app.command()
def extract():
    uvloop.run(async_extract())


@app.command()
def analyze():

    from repositories.entity_storage import FilmStorageHandler, PersonStorageHandler
    from repositories.html_analyzer import HtmlAnalyzer
    from repositories.raw_content_storage import HtmlContentStorageHandler
    from settings import Settings
    from use_cases.analyze_html import HtmlAnalysisUseCase

    settings = Settings()
    film_storage_handler = FilmStorageHandler(settings=settings)
    person_strorage_handler = PersonStorageHandler(settings=settings)
    raw_content_storage_handler = HtmlContentStorageHandler(
        path=settings.persistence_directory / "html"
    )
    analyzer = HtmlAnalyzer()

    uc = HtmlAnalysisUseCase(
        film_storage_handler=film_storage_handler,  # where films will be saved
        person_storage_handler=person_strorage_handler,  # where persons will be saved
        raw_content_storage_handler=raw_content_storage_handler,  # where raw html can be found
        analyzer=analyzer,
        settings=settings,
    )
    uc.execute(wait_for_completion=True)

    print("Analysis completed.")


@app.command()
def index():

    from entities.film import Film
    from entities.person import Person
    from repositories.entity_storage import FilmStorageHandler, PersonStorageHandler
    from repositories.meili_indexer import MeiliIndexer
    from settings import Settings
    from use_cases.index_films import IndexerUseCase

    settings = Settings()
    film_storage_handler = FilmStorageHandler(settings=settings)
    person_storage_handler = PersonStorageHandler(settings=settings)

    uc = IndexerUseCase(
        indexer=MeiliIndexer[Film](settings=settings),
        storage_handler=film_storage_handler,
    )
    uc.execute(
        wait_for_completion=False,  # don't wait for the task to complete; return immediately
    )
    print("Films Indexation completed.")

    uc = IndexerUseCase(
        indexer=MeiliIndexer[Person](settings=settings),
        storage_handler=person_storage_handler,
    )
    uc.execute(
        wait_for_completion=False,  # don't wait for the task to complete; return immediately
    )

    print("Persons Indexation completed.")


@app.command()
async def async_extract():

    from repositories.raw_content_storage import HtmlContentStorageHandler
    from settings import Settings
    from use_cases.scrape_wikipedia import WikipediaDownloadUseCase

    start_time = time.time()
    print("Starting scraping...")

    settings = Settings()
    storage_handler = HtmlContentStorageHandler(
        path=settings.persistence_directory / "html"
    )

    scraping_use_case = WikipediaDownloadUseCase(
        settings=settings,
        storage_handler=storage_handler,
    )

    await scraping_use_case.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    print("Scraping completed in %.2f seconds." % elapsed_time)


if __name__ == "__main__":

    app()
