from typing import Any

from prefect import Task, get_run_logger
from prefect.client.schemas.objects import TaskRun
from prefect.states import State

from src.exceptions import HttpError, RetrievalError, SummaryError

RETRY_ATTEMPTS: int = 30
RETRY_DELAY_SECONDS: list[int] = [
    0.1 * ((i**2) / 8) for i in range(RETRY_ATTEMPTS)
]  # exponential backoff


def is_http_task_retriable(
    task: Task[..., Any], task_run: TaskRun, state: State[Any]
) -> bool:
    """determine if a task related to a HTTP response should be retried"""
    logger = get_run_logger()
    try:
        state.result()
    except Exception as e:
        if isinstance(e, HttpError) and e.status_code >= 429:
            logger.warning(f"HTTP error with status {e.status_code} will be retried")
            return True
        elif isinstance(e, HttpError):
            logger.warning(
                f"HTTP error with status {e.status_code} will not be retried"
            )
            return False
        elif isinstance(e, TimeoutError):
            logger.warning("Timeout error will be retried")
            return True
        else:
            logger.error(f"Exception is not retriable: {e}")

    return False


def is_extraction_task_retriable(
    task: Task[..., Any], task_run: TaskRun, state: State[Any]
) -> bool:
    """determine if a task related to a HTTP response should be retried"""
    logger = get_run_logger()
    try:
        state.result()
    except Exception as e:

        if isinstance(e, (SummaryError, RetrievalError)):
            logger.warning(
                f"Task '{task.name}' will be retried due to exception {type(e).__name__}"
            )
            return True
        elif isinstance(e, TimeoutError):
            logger.warning(f"Timeout on task '{task.name}' will be retried")
            return True
        else:
            logger.error(
                f"Task '{task.name}' will NOT be retried due to exception '{type(e).__name__}'"
            )

    return False
