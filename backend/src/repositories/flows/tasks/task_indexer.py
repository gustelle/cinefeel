from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import PrefectFuture

from src.entities.component import EntityComponent
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.repositories.search.meili_indexer import MeiliIndexer
from src.settings import Settings


class IndexerFlow(ITaskExecutor):

    entity_type: type[EntityComponent]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[EntityComponent]):
        self.settings = settings
        self.entity_type = entity_type

    @task(cache_policy=NO_CACHE)
    def index_batch(
        self,
        films: list[EntityComponent],
        indexer: IStorageHandler,
    ) -> None:
        """
        Index a batch of `Storable` using the provided indexer.
        """
        indexer.insert_many(
            contents=films,
            wait_for_completion=False,
        )

    @flow(
        name="index",
    )
    def execute(
        self,
    ) -> None:

        logger = get_run_logger()

        storage_handler = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )
        indexer = MeiliIndexer[self.entity_type](settings=self.settings)

        # upsert in batches
        last_ = None
        has_more = True
        batch_size = 100

        futures = []

        while has_more:

            batch = storage_handler.query(
                order_by="uid",
                after=last_,
                limit=batch_size,
            )

            futures.append(self.index_batch.submit(batch, indexer))

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

        future: PrefectFuture
        for future in futures:
            try:
                future.result(timeout=5, raise_on_failure=True)
            except TimeoutError:
                logger.warning(
                    f"Task timed out for {future.task_run_id}, skipping storage."
                )
            except Exception as e:
                logger.error(f"Error in task execution: {e}")

        logger.info("'index_films' Flow completed successfully.")
