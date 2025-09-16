import sys
from typing import Optional

import typer
from loguru import logger

from src.settings import Settings
from src.use_cases.db_storage import DBStorageType
from src.use_cases.extract import ExtractionType
from src.use_cases.scrape import ScrapingType

app = typer.Typer()


@app.command()
def scrape(type: Optional[ScrapingType] = None):

    from src.use_cases.scrape import ScrapingUseCase

    uc = ScrapingUseCase(
        settings=Settings(),
        types=[type.value] if type else list(ScrapingType),
    )
    uc.execute()


@app.command()
def extract(type: Optional[ExtractionType] = None):
    """for debugging only, to run the extraction flow directly without needing to deploy it first

    Example usage:
        python main.py extract --type movies
        python main.py extract --type persons
        python main.py extract # runs both types
    """

    from src.use_cases.extract import EntityExtractionUseCase

    uc = EntityExtractionUseCase(
        settings=Settings(),
        types=[type.value] if type else list(ExtractionType),
    )
    uc.execute()


@app.command()
def store(type: Optional[DBStorageType] = None):

    from src.use_cases.db_storage import DBStorageUseCase

    uc = DBStorageUseCase(
        settings=Settings(),
        types=[type.value] if type else list(DBStorageType),
    )
    uc.execute()


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
