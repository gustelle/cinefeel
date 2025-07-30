from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE

from src.entities.composable import Composable
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class SearchIndexerFlow(ITaskExecutor):

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

    def execute(
        self,
        input_storage: IStorageHandler[Composable],
        output_storage: IStorageHandler[Composable],
    ):

        logger = get_run_logger()

        # upsert in batches
        last_ = None
        has_more = True
        batch_size = 100

        futures = []

        while has_more:

            batch = input_storage.query(
                order_by="uid",
                after=last_,
                limit=batch_size,
            )

            futures.append(self.index_batch.submit(batch, output_storage))

            if batch is None or len(batch) == 0:
                logger.info(
                    f"Reached the last batch: {len(batch)} films, no more to process"
                )
                has_more = False
            elif last_ is not None and last_.uid == batch[-1].uid:
                logger.info(
                    f"Reached the last batch: {len(batch)} films, no more to process"
                )
                has_more = False
            else:
                last_ = batch[-1]
                logger.info(f"Next batch starting after '{last_.uid}'")

        for future in futures:
            try:
                future.result(timeout=self.settings.task_timeout, raise_on_failure=True)
            except TimeoutError:
                logger.warning(f"Task timed out for {future.task_run_id}.")
            except Exception as e:
                logger.error(f"Error in task execution: {e}")

        logger.info("'index_films' Flow completed successfully.")
