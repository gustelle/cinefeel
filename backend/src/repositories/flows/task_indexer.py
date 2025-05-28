from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import PrefectFuture

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.indexer import IDocumentIndexer
from src.repositories.search.meili_indexer import MeiliIndexer
from src.repositories.storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings


class IndexerFlowRunner[T: Film | Person]:

    entity_type: type[T]
    settings: Settings

    def __init__(self, settings: Settings):
        self.settings = settings

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type

        return new_cls

    @task(cache_policy=NO_CACHE)
    def index_batch(
        self,
        films: list[T],
        indexer: IDocumentIndexer,
    ) -> None:
        """
        TODO: index persons in a separate index

        Args:
            wait_for_completion (bool, optional): _description_. Defaults to False.
        """
        indexer.insert_or_update(
            docs=films,
            wait_for_completion=False,
        )

    @flow(
        name="index",
    )
    def index(
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
