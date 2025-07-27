from prefect import flow

from src.entities.composable import Composable
from src.entities.film import Film
from src.interfaces.pipeline import IPipelineRunner
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.http.sync_http import SyncHttpClient
from src.repositories.task_orchestration.flows.task_relationship_storage import (
    RelationshipFlow,
)
from src.settings import Settings


class RelationshipProcessor(IPipelineRunner):
    """
    Reads Entities (Film or Person) from the storage,
    and analyzes their content to identify relationships between them.
    """

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Composable]):
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

        # needed to retrieve permalinks by name
        http_client = SyncHttpClient(settings=self.settings)

        # where to store the relationships
        db_storage = (
            FilmGraphHandler(
                settings=self.settings,
            )
            if self.entity_type is Film
            else PersonGraphHandler(
                settings=self.settings,
            )
        )

        RelationshipFlow(
            settings=self.settings,
            http_client=http_client,
        ).execute(
            input_storage=db_storage,
            output_storage=db_storage,
        )
