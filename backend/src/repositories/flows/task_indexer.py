from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE

from src.entities.film import Film
from src.interfaces.indexer import IDocumentIndexer
from src.repositories.search.meili_indexer import MeiliIndexer
from src.repositories.storage.json_storage import JSONFilmStorageHandler
from src.settings import Settings

CONCURRENCY = 4


@task(cache_policy=NO_CACHE)
def index_batch(
    films: list[Film],
    indexer: IDocumentIndexer,
) -> None:
    """
    TODO: index persons in a separate index

    Args:
        wait_for_completion (bool, optional): _description_. Defaults to False.
    """
    indexer.insert_or_update(
        docs=films,
        wait_for_completion=False,
    )


@flow()
def index_films(
    settings: Settings,
) -> None:

    logger = get_run_logger()

    storage_handler = JSONFilmStorageHandler(settings=settings)
    indexer = MeiliIndexer[Film](settings=settings)

    # upsert in batches
    last_ = None
    has_more = True
    batch_size = 100

    while has_more:

        batch = storage_handler.query(
            order_by="uid",
            after=last_,
            limit=batch_size,
        )

        index_batch(batch, indexer)

        if batch is None or len(batch) == 0:
            logger.info(f"Last batch: {len(batch)} films")
            has_more = False
        else:
            last_ = batch[-1]
            logger.info(f"Next batch starting after '{last_.uid}'")

    logger.info("Flow completed successfully.")
