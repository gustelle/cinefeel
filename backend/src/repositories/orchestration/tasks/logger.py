from logging import Logger

from loguru import logger as loguru_logger
from prefect import get_run_logger
from prefect.context import MissingContextError


def get_logger() -> Logger:
    """
    Get a logger compatible with Prefect tasks, with a fallback to loguru
    if not in a Prefect task context.

    Args:
        name (str): The name of the logger.
    Returns:
        Logger: The configured logger instance.
    """
    try:
        # Try to get Prefect's task logger
        return get_run_logger()
    except MissingContextError:
        # Fallback to loguru logger if not in a Prefect task context
        return loguru_logger
