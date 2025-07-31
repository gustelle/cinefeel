from typing import Any

from prefect import Task, get_run_logger
from prefect.client.schemas.objects import TaskRun
from prefect.states import State

from src.interfaces.http_client import HttpError


def is_task_retriable(
    task: Task[..., Any], task_run: TaskRun, state: State[Any]
) -> bool:
    logger = get_run_logger()
    try:
        state.result()
    except Exception as e:
        if isinstance(e, HttpError) and e.status_code >= 429:
            return True
        elif isinstance(e, HttpError):
            logger.warning(
                f"HTTP error with status {e.status_code} will not be retried"
            )
            return False
        else:
            logger.error(f"Exception is not retriable: {e}")
    return False
