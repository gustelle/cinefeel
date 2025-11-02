import time

from prefect import get_run_logger
from prefect.futures import PrefectFuture


def _is_safe_done(future: PrefectFuture) -> bool:

    logger = get_run_logger()
    try:
        future.result()
    except Exception:
        # do nothing
        logger.error(
            f"Error occurred while waiting for task '{future._task_run_id}': {future.state.message}"
        )
    finally:
        return future.state.is_final()


def wait_for_all(
    tasks: list[PrefectFuture],
) -> tuple[set[PrefectFuture], set[PrefectFuture]]:
    """
    Waits for a list of Prefect tasks to really complete, handling exceptions for each task individually,
    and handling case of tasks in PENDING state.

    PENDING tasks are relaunched until they complete successfully or fail.

    Args:
        tasks (list[PrefectFuture]): A list of PrefectFuture objects representing the tasks to wait for.

    Returns:
        tuple[set[PrefectFuture], set[PrefectFuture]]: A tuple containing two sets:
            - The first set contains the completed tasks.
            - The second set contains the tasks that failed with exceptions.
    """

    logger = get_run_logger()

    completed_tasks = set()
    failed_tasks = set()
    pending_tasks: set[PrefectFuture] = set(tasks)

    # now wait for pending tasks
    while pending_tasks:

        current_pending = pending_tasks.copy()
        pending_tasks.clear()

        for future in current_pending:
            if _is_safe_done(future):
                if future.state.is_completed():
                    completed_tasks.add(future)
                elif future.state.is_pending():
                    pending_tasks.add(future)
                else:
                    failed_tasks.add(future)

        logger.info(
            f"Waiting for {len(pending_tasks)} pending tasks to complete...sleeping"
        )
        time.sleep(1)  # avoid busy waiting

    logger.info(
        f"All tasks completed: {len(completed_tasks)}, failed: {len(failed_tasks)}"
    )

    return completed_tasks, failed_tasks
