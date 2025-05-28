import time

import typer
import uvloop
from loguru import logger

from src.settings import Settings

app = typer.Typer()


@app.command()
def films():
    uvloop.run(async_run_films())


async def async_run_films():

    from src.use_cases.analyze_films import WikipediaFilmAnalysisUseCase

    start_time = time.time()
    logger.info("Starting scraping...")

    uc = WikipediaFilmAnalysisUseCase(
        settings=Settings(),
    )
    await uc.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info(
        "WikipediaFilmAnalysisUseCase completed in %.2f seconds." % elapsed_time
    )


@app.command()
def persons():
    uvloop.run(async_run_persons())


async def async_run_persons():

    from src.use_cases.analyze_persons import WikipediaPersonAnalysisUseCase

    start_time = time.time()
    logger.info("Starting scraping...")

    uc = WikipediaPersonAnalysisUseCase(
        settings=Settings(),
    )
    await uc.execute()

    end_time = time.time()
    elapsed_time = end_time - start_time

    logger.info(
        "WikipediaPersonAnalysisUseCase completed in %.2f seconds." % elapsed_time
    )


if __name__ == "__main__":
    app()
