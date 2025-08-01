import sys

import typer
from loguru import logger

from src.settings import Settings

app = typer.Typer()


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
