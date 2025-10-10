from datetime import timedelta

from prefect import get_run_logger, task
from prefect.futures import wait

from src.entities.composable import Composable
from src.entities.movie import Movie
from src.interfaces.task import ITaskExecutor
from src.repositories.db.local_storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings


class FeatureExtractionTask(ITaskExecutor):
    """
    flow in charge of setting flags on entities, e.g. to indicate
    if a poster contains a black person or not....
    """

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Composable]):
        self.settings = settings
        self.entity_type = entity_type

    @task(task_run_name="to_db-{entity.uid}", tags=["cinefeel_tasks"])
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

    @task(task_run_name="extract_features-{entity.uid}", tags=["cinefeel_tasks"])
    def extract_features(self, entity: Composable) -> Composable:
        """
        Analyze the relationships of a single entity.
        This method should be implemented to analyze the relationships
        and store them in the graph database.
        """
        logger = get_run_logger()
        logger.info(f"Extracting features for '{entity.uid}'")

        if self.entity_type == Movie:
            # extract features from the poster
            # e.g. if the poster contains a black person or not
            ...

        return entity

    @task()
    def execute_task(
        self,
    ) -> None:

        local_storage_handler = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        _futures = []

        for uid, entity in local_storage_handler.scan():

            _futures.append(
                self.to_db.submit(
                    # storage=json_p_storage,
                    entity=self.extract_features.with_options(
                        cache_key_fn=lambda *_: f"extract_features-{uid}",
                        cache_expiration=timedelta(hours=1),  # 1 hour
                    ).submit(
                        entity=entity,
                    ),
                )
            )

        wait(_futures)
