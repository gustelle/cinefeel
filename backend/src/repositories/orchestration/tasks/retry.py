from typing import Any

from prefect import Task, get_run_logger
from prefect.client.schemas.objects import TaskRun
from prefect.states import State
from ratelimit import RateLimitException

from src.exceptions import HttpError

RETRY_ATTEMPTS: int = 30
RETRY_DELAY_SECONDS: list[int] = [0.1, 0.5, 1]


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
        elif isinstance(e, RateLimitException):
            logger.warning("Rate limit exceeded, error will be retried")
            return True
        else:
            logger.error(f"Exception is not retriable: {e}")
    return False
