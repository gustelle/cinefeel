from prefect import flow, task
from prefect.cache_policies import NO_CACHE

from src.entities.component import EntityComponent
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class GraphDatabaseFlow(ITaskExecutor):

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
        pass

        # logger = get_run_logger()

        # storage_handler = JSONEntityStorageHandler[self.entity_type](
        #     settings=self.settings
        # )

        # # upsert in batches
        # last_ = None
        # has_more = True
        # batch_size = 100

        # futures = []

        # while has_more:

        #     batch = storage_handler.query(
        #         order_by="uid",
        #         after=last_,
        #         limit=batch_size,
        #     )

        # Iterate over the batch
        # pass the batch to the graph database
        # and insert it
