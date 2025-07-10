
import dask
from prefect import flow, get_run_logger
from prefect.futures import PrefectFuture
from prefect_dask import DaskTaskRunner

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.pipeline import IPipelineRunner
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
    ) -> PrefectFuture:
        """
        Run the pipeline to analyze relationships between entities.
        """
        logger = get_run_logger()

        # Load entities from storage
        entity_storage = self.settings.get_entity_storage(self.entity_type)
        entities = entity_storage.load_all()

        if not entities:
            logger.warning(f"No entities found for {self.entity_type.__name__}.")
            return None

        # Analyze relationships using Dask
        futures = [
            dask.delayed(self.analyze_relationships)(entity) for entity in entities
        ]
        results = dask.compute(*futures)

        return results
