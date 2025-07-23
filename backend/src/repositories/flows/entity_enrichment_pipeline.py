from prefect import flow

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.pipeline import IPipelineRunner
from src.repositories.flows.tasks.task_relationship import RelationshipFlow
from src.repositories.http.sync_http import SyncHttpClient
from src.settings import Settings


class EntityEnrichmentProcessor(IPipelineRunner):
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
        name="Enrichment Flow",
    )
    def execute_pipeline(
        self,
    ) -> None:
        """
        Run the pipeline to analyze relationships between entities.
        """
        http_client = SyncHttpClient(settings=self.settings)

        RelationshipFlow(
            settings=self.settings,
            entity_type=self.entity_type,
            http_client=http_client,
        ).execute()

        # FeatureExtractionFlow(
        #     settings=self.settings,
        #     entity_type=self.entity_type,
        # ).execute()
