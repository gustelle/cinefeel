from prefect import flow
from prefect_dask import DaskTaskRunner

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.pipeline import IPipelineRunner
from src.repositories.flows.tasks.task_feature_extraction import (
    ComposableFeatureExtractionFlow,
)
from src.repositories.flows.tasks.task_relationship import RelationshipFlow
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
        RelationshipFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute()

        ComposableFeatureExtractionFlow(
            settings=self.settings,
            entity_type=self.entity_type,
        ).execute()
