import sys
from typing import Optional

import typer
from loguru import logger

from src.settings import AppSettings
from src.use_cases.uc_types import EntityType

app = typer.Typer()


@app.command()
def scrape(type: Optional[EntityType] = None):

    from src.use_cases.scrape import ScrapingUseCase

    uc = ScrapingUseCase(
        app_settings=AppSettings(),
        types=[type.value] if type else list(EntityType),
    )
    uc.execute()


@app.command()
def extract(type: Optional[EntityType] = None):
    """
    Example usage:
        python main.py extract --type movies
        python main.py extract --type persons
        python main.py extract # runs both types
    """

    from src.use_cases.extract import EntityExtractionUseCase

    uc = EntityExtractionUseCase(
        app_settings=AppSettings(),
        types=[type.value] if type else list(EntityType),
    )
    uc.execute()


@app.command()
def store(type: Optional[EntityType] = None):
    """Store extracted entities in the database.

    Args:
        type (Optional[EntityType], optional): The type of entities to store. Defaults to None.

    Example usage:
        python main.py store --type movies
        python main.py store --type persons
        python main.py store # runs both types
    """

    from src.use_cases.db_storage import DBStorageUseCase

    uc = DBStorageUseCase(
        app_settings=AppSettings(),
        types=[type.value] if type else list(EntityType),
    )
    uc.execute()


@app.command()
def connect(type: Optional[EntityType] = None):
    """Connect entities in the database.
    Args:
        type (Optional[EntityType], optional): The type of entities to connect. Defaults to None.
    Example usage:
        python main.py connect --type movies
        python main.py connect --type persons
        python main.py connect # runs both types
    """

    from src.use_cases.connect import EntitiesConnectionUseCase

    uc = EntitiesConnectionUseCase(
        app_settings=AppSettings(),
        types=[type.value] if type else list(EntityType),
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
