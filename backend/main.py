import time

import typer
import uvloop
from loguru import logger

from src.settings import Settings

app = typer.Typer()


@app.command()
def flow():
    uvloop.run(async_run_flow())


async def async_run_flow():
    """
    Run the entire flow: crawl, extract, and index.
    """

    from src.use_cases.flow_uc import WikipediaFilmAnalysisUseCase

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


if __name__ == "__main__":

    app()
