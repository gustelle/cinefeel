from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import wait

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class SearchUpdater(ITaskExecutor):
    """Updates a search index with new content."""

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Composable]):
        self.settings = settings
        self.entity_type = entity_type

    @task(cache_policy=NO_CACHE)
    def index_batch(
        self,
        entities: list[Composable],
        indexer: IStorageHandler,
    ) -> None:
        """
        Index a batch of `Storable` using the provided indexer.
        """
        indexer.insert_many(
            contents=entities,
            wait_for_completion=False,
        )

    @task(
        cache_policy=NO_CACHE, retries=3, retry_delay_seconds=5, tags=["cinefeel_tasks"]
    )
    def execute(
        self,
        input_storage: IStorageHandler[Composable],
        output_storage: IStorageHandler[Composable],
    ):

        logger = get_run_logger()

        batch_size = 100

        futures = []
        batch: list[Composable] = []

        try:

            while res := next(input_storage.scan()):

                batch.append(res)

                if len(batch) >= batch_size:
                    logger.info(f"Processing batch of {len(batch)} entities")
                    futures.append(self.index_batch.submit(batch, output_storage))
                    batch = []
        except StopIteration:
            if batch:
                logger.info(f"Processing final batch of {len(batch)} entities")
                futures.append(self.index_batch.submit(batch, output_storage))

        wait(futures)
