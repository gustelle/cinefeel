from interfaces.indexer import IDocumentIndexer
from interfaces.storage import IStorageHandler


class IndexerUseCase:

    _indexer: IDocumentIndexer

    _storage_handler: IStorageHandler

    def __init__(
        self,
        indexer: IDocumentIndexer,
        storage_handler: IStorageHandler,
    ):
        self._storage_handler = storage_handler
        self._indexer = indexer

    def execute(self, wait_for_completion: bool = False):
        """
        TODO: index persons in a separate index

        Args:
            wait_for_completion (bool, optional): _description_. Defaults to False.
        """

        # upsert in batches
        last_ = None
        has_more = True
        batch_size = 100

        while has_more:

            batch = self._storage_handler.query(
                order_by="uid",
                after=last_,
                limit=batch_size,
            )

            self._indexer.upsert(
                docs=batch,
                wait_for_completion=wait_for_completion,
            )

            if batch is None or len(batch) == 0:
                print(f"Last batch: {len(batch)} films")
                has_more = False
            else:
                last_ = batch[-1]
                print(f"Next batch starting after '{last_.uid}'")
