import sys
from typing import Optional

import typer
from loguru import logger

from src.settings import Settings
from src.use_cases.extract import ExtractionType

app = typer.Typer()


@app.command()
def extract(type: Optional[ExtractionType] = None):
    """for debugging only, to run the extraction flow directly without needing to deploy it first

    Example usage:
        python main.py extract --type movies
        python main.py extract --type persons
        python main.py extract # runs both types
    """

    from src.use_cases.extract import ExtractUseCase

    uc = ExtractUseCase(
        settings=Settings(),
        types=[type.value] if type else list(ExtractionType),
    )
    uc.execute()


@app.command()
def serve():

    from src.use_cases.serve import ServeUseCase

    uc = ServeUseCase(
        settings=Settings(),
    )
    uc.execute()


@app.command()
def deploy():

    from src.use_cases.deploy import DeployFlowsUseCase

    uc = DeployFlowsUseCase(
        settings=Settings(),
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
