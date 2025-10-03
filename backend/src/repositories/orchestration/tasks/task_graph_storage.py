from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import wait

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class DBStorageTask(ITaskExecutor):
    """Updates a database storage with new content."""

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
        )

    @task(cache_policy=NO_CACHE)
    def query_input_storage(
        self,
        input_storage: IStorageHandler[Composable],
        after: str | None = None,
        limit: int = 100,
        order_by: str = "uid",
    ) -> list[Composable]:
        """
        Wraps the query with a task decorator to allow Prefect to manage retries.
        """
        return input_storage.query(
            order_by=order_by,
            after=after,
            limit=limit,
        )

    @task(
        cache_policy=NO_CACHE,
    )
    def execute(
        self,
        input_storage: IStorageHandler[Composable],
        output_storage: IStorageHandler[Composable],
    ) -> None:

        logger = get_run_logger()

        # upsert in batches
        last_ = None
        has_more = True
        batch_size = 100

        futures = []

        while has_more:

            batch_promise = self.query_input_storage.submit(
                input_storage=input_storage,
                after=last_,
                limit=batch_size,
            )
            batch = batch_promise.result(
                timeout=self.settings.prefect_task_timeout, raise_on_failure=True
            )

            if batch is None or len(batch) == 0:
                logger.info(
                    f"Reached the last batch: {len(batch)} movies, no more to process"
                )
                has_more = False
            elif last_ is not None and last_.uid == batch[-1].uid:
                logger.info(
                    f"Reached the last batch: {len(batch)} movies, no more to process"
                )
                has_more = False
            else:
                last_ = batch[-1]
                logger.info(f"Next batch starting after '{last_.uid}'")

            futures.append(self.index_batch.submit(batch, output_storage))

        wait(futures)
