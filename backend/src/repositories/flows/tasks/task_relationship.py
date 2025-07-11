import dask
from loguru import logger
from prefect import flow, get_run_logger, task
from prefect.futures import PrefectFuture

from src.entities.composable import Composable
from src.interfaces.task import ITaskExecutor
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings


class RelationshipFlow(ITaskExecutor):
    """
    flow in charge of finding relationships between entities.
    and storing them into the graph database.

    This flow starts from json files stored in the local storage.
    """

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Composable]):
        self.settings = settings
        self.entity_type = entity_type

    @task(task_run_name="to_db-{entity.uid}")
    def to_db(self, entity: Composable) -> Composable:
        """
        Analyze the relationships of a single entity.
        This method should be implemented to analyze the relationships
        and store them in the graph database.
        """
        logger = get_run_logger()
        logger.info(f"Storing {entity.uid} into the graph database")

        # Here you would implement the logic to analyze relationships
        # For example, you might query a graph database or perform some analysis
        # and then store the results back into the graph database.
        return entity

    @task(task_run_name="analyze_relationships-{entity.uid}")
    def analyze_relationships(self, entity: Composable) -> Composable:
        """
        Analyze the relationships of a single entity.
        This method should be implemented to analyze the relationships
        and store them in the graph database.
        """
        logger = get_run_logger()
        logger.info(f"Analyzing relationships for {entity.uid}")

        # Here you would implement the logic to analyze relationships
        # For example, you might query a graph database or perform some analysis
        # and then store the results back into the graph database.
        return entity

    @flow(
        name="find_relationships",
    )
    def execute(
        self,
    ) -> None:

        local_storage_handler = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        # send concurrent tasks to analyze HTML content
        # don't wait for the task to be completed
        storage_futures = []

        # need to keep track of the futures to wait for them later
        # see: https://github.com/PrefectHQ/prefect/issues/17517
        entity_futures = []

        # analyze the HTML content
        with (
            dask.annotate(resources={"GPU": 1}),
            dask.config.set({"array.chunk-size": "512 MiB"}),
        ):

            for entity in local_storage_handler.scan():

                future_entity = self.analyze_relationships.submit(
                    entity=entity,
                )
                entity_futures.append(future_entity)

                storage_futures.append(
                    self.to_db.submit(
                        # storage=json_p_storage,
                        entity=future_entity,
                    )
                )

            # now wait for all tasks to complete
            future_storage: PrefectFuture
            for future_storage in storage_futures:
                try:
                    future_storage.result(
                        raise_on_failure=True, timeout=self.settings.task_timeout
                    )
                except TimeoutError:
                    logger.warning(f"Task timed out for {future_storage.task_run_id}.")
                except Exception as e:
                    logger.error(f"Error in task execution: {e}")

        # Iterate over the batch
        # pass the batch to the graph database
        # and insert it
