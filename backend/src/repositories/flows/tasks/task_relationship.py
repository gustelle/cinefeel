from prefect import flow

from src.entities.component import EntityComponent
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class RelationshipFlow(ITaskExecutor):
    """
    flow in charge of finding relationships between entities.
    and storing them into the graph database.

    This flow starts from json files stored in the local storage.
    """

    entity_type: type[EntityComponent]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: type[EntityComponent]):
        self.settings = settings
        self.entity_type = entity_type

    @flow(
        name="find_relationships",
    )
    def execute(
        self,
    ) -> None:
        pass
        # logger = get_run_logger()

        # storage_handler = JSONEntityStorageHandler[self.entity_type](
        #     settings=self.settings
        # )

        # # scan the storage to find all entities

        # while has_more:

        #     batch = storage_handler.query(
        #         order_by="uid",
        #         after=last_,
        #         limit=batch_size,
        #     )

        # Iterate over the batch
        # pass the batch to the graph database
        # and insert it
