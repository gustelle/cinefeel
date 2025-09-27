from typing import Literal

from prefect import flow
from prefect.futures import wait

from src.entities.movie import Movie
from src.entities.person import Person
from src.repositories.db.graph.mg_movie import MovieGraphRepository
from src.repositories.db.graph.mg_person import PersonGraphRepository
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.orchestration.tasks.task_graph_storage import DBStorageTask
from src.repositories.orchestration.tasks.task_indexer import SearchIndexerTask
from src.repositories.search.meili_indexer import MeiliHandler
from src.settings import Settings


@flow(
    name="db_storage_flow",
    description="Store extracted entities into a storage backend.",
)
def db_storage_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
) -> None:
    """
    TODO:
    - mark entities as "processed" to avoid re-processing them
    - pass a param to re-process all entities if needed (a bit like a "force" flag)
    """

    tasks = []

    match entity_type:
        case "Movie":
            _entity_type = Movie
        case "Person":
            _entity_type = Person
        case _:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    json_store = RedisJsonStorage[_entity_type](settings=settings)

    if settings.search_base_url:
        search_flow = SearchIndexerTask(
            settings=settings,
            entity_type=_entity_type,
        )

        # for all pages
        tasks.append(
            search_flow.execute.submit(
                input_storage=json_store,
                output_storage=MeiliHandler[_entity_type](settings=settings),
            )
        )

    if settings.graph_db_uri:

        storage_flow = DBStorageTask(
            settings=settings,
            entity_type=_entity_type,
        )

        db_handler = (
            MovieGraphRepository(settings=settings)
            if _entity_type is Movie
            else PersonGraphRepository(settings=settings)
        )

        tasks.append(
            storage_flow.execute.submit(
                input_storage=json_store,
                output_storage=db_handler,
            )
        )

    wait(tasks)
