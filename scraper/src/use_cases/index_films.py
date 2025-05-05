from interfaces.storage import IStorageHandler
from repositories.meili_indexer import MeiliIndexer
from settings import Settings


class MeiliIndexerUseCase:

    indexer: MeiliIndexer
    storage_handler: IStorageHandler

    def __init__(self, persistence_handler: IStorageHandler, settings: Settings = None):
        self.settings = settings or Settings()
        self.storage_handler = persistence_handler
        self.indexer = MeiliIndexer(
            settings=self.settings,
        )

    def execute(self, wait_for_completion: bool = False):

        # upsert in batches
        last_film = None
        has_more = True
        batch_size = 100

        while has_more:

            batch = self.storage_handler.query(
                order_by="uid",
                after_film=last_film,
                limit=batch_size,
            )

            self.indexer.upsert(
                docs=batch,
                wait_for_completion=wait_for_completion,
            )

            if batch is None or len(batch) == 0:
                print(f"Last batch: {len(batch)} films")
                has_more = False
            else:
                last_film = batch[-1]
                print(f"Next batch starting after '{last_film.uid}'")
