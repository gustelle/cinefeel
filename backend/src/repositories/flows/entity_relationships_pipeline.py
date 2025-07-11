from prefect import flow, get_run_logger
from prefect_dask import DaskTaskRunner

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.pipeline import IPipelineRunner
from src.repositories.db.graph_storage import GraphDBStorage
from src.settings import Settings


class EntityRelationshipProcessor(IPipelineRunner):
    """
    Reads Entities (Film or Person) from the storage,
    and analyzes their content to identify relationships between them.
    """

    entity_type: type[Film | Person]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Film | Person]):
        self.entity_type = entity_type
        self.settings = settings

    @flow(
        name="Relationships Analysis Flow",
        task_runner=DaskTaskRunner(),
    )
    def execute_pipeline(
        self,
    ) -> None:
        """
        Run the pipeline to analyze relationships between entities.
        """
        logger = get_run_logger()

        # Load entities from graph database
        entity_storage = GraphDBStorage[self.entity_type](self.settings)
        for entity in entity_storage.scan():
            logger.info(f"Loaded entity: {entity.uid}")

        # if not entities:
        #     logger.warning(f"No entities found for {self.entity_type.__name__}.")
        #     return None

        # # Analyze relationships using Dask
        # futures = [
        #     dask.delayed(self.analyze_relationships)(entity) for entity in entities
        # ]
        # results = dask.compute(*futures)

        # return results
