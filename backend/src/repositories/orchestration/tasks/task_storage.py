from logging import Logger

from prefect import task

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler

from .logger import get_logger


@task(
    name="Batch Insert Task",
    description="Scans an input storage and batch inserts entities into an output storage.",
)
def execute_task(
    input_storage: IStorageHandler[Composable],
    output_storage: IStorageHandler[Composable],
    batch_size: int = 100,
):

    logger: Logger = get_logger()

    batch: list[Composable] = []

    for _, res in input_storage.scan():

        batch.append(res)

        if len(batch) >= batch_size:
            output_storage.insert_many(
                contents=batch,
            )
            batch = []

    if batch:
        logger.info(f"Processing final batch of {len(batch)} entities")
        output_storage.insert_many(
            contents=batch,
        )
