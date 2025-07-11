from prefect import flow

from src.entities.composable import Composable
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class ComposableFeatureExtractionFlow(ITaskExecutor):
    """
    flow in charge of setting flags on entities, e.g. to indicate
    if a poster contains a black person or not....
    """

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[Composable]):
        self.settings = settings
        self.entity_type = entity_type

    @flow(
        name="extract_features-{entity_type.__name__}",
    )
    def execute(
        self,
    ) -> None:

        pass

        # Iterate over the batch
        # pass the batch to the graph database
        # and insert it
