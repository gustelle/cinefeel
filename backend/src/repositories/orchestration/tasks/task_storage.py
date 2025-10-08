from prefect import get_run_logger, task

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class BatchInsertTask(ITaskExecutor):
    """
    Scans an input storage and batch inserts entities into an output storage.
    """

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Composable]):
        self.settings = settings
        self.entity_type = entity_type

    @task()
    def execute(
        self,
        input_storage: IStorageHandler[Composable],
        output_storage: IStorageHandler[Composable],
        batch_size: int = 100,
    ):

        logger = get_run_logger()

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
