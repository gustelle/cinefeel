from prefect import flow, get_run_logger

from src.interfaces.task import ITaskExecutor


@flow
def process_flow(task_executor: ITaskExecutor, *args, **kwargs) -> None:
    """thin wrapper around the task executor's execute method
    this is required to deploy/serve prefect flows,
    because class flows cannot be deployed directly because of the `self` reference.
    """

    logger = get_run_logger()

    logger.info(args)
    logger.info(kwargs)

    task_executor.execute(*args, **kwargs)
