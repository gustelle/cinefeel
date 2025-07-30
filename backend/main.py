import sys
import time

import typer
import uvloop
from loguru import logger

from src.settings import Settings

app = typer.Typer()


@app.command()
def extract_movies():
    #
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(async_run_films())

    # async def async_run_films():

    from src.use_cases.extract_films import WikipediaFilmExtractionUseCase

    start_time = time.time()
    logger.info("Starting scraping...")

    uc = WikipediaFilmExtractionUseCase(
        settings=Settings(),
    )
    # await
    uc.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info(
        "WikipediaFilmAnalysisUseCase completed in %.2f seconds." % elapsed_time
    )


@app.command()
def extract_persons():
    uvloop.run(async_run_persons())


async def async_run_persons():

    from src.use_cases.extract_persons import WikipediaPersonExtractionUseCase

    start_time = time.time()
    logger.info("Starting scraping...")

    uc = WikipediaPersonExtractionUseCase(
        settings=Settings(),
    )
    await uc.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info(
        "WikipediaPersonAnalysisUseCase completed in %.2f seconds." % elapsed_time
    )


@app.command()
def enrich():

    from src.use_cases.enrich import EnrichmentUseCase

    start_time = time.time()
    logger.info("Starting enrichment processing...")

    uc = EnrichmentUseCase(
        settings=Settings(),
    )
    uc.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info("EnrichmentUseCase completed in %.2f seconds." % elapsed_time)


if __name__ == "__main__":

    # configure logging
    logger.remove()

    logger.add(
        "logs/{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

    logger.add(
        sys.stderr,
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

    logger.info("Starting application...")

    app()
