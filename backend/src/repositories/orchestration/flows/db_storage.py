from typing import Literal

from prefect import flow
from prefect.futures import wait

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.graph.film_graph import FilmGraphHandler
from src.repositories.db.graph.person_graph import PersonGraphHandler
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.orchestration.tasks.task_graph_storage import DBStorageUpdater
from src.repositories.orchestration.tasks.task_indexer import SearchUpdater
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

    tasks = []

    match entity_type:
        case "Movie":
            entity_type = Film
        case "Person":
            entity_type = Person
        case _:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    json_store = RedisJsonStorage[entity_type](settings=settings)

    if settings.meili_base_url:
        search_flow = SearchUpdater(
            settings=settings,
            entity_type=entity_type,
        )

        # for all pages
        tasks.append(
            search_flow.execute.submit(
                input_storage=json_store,
                output_storage=MeiliHandler[entity_type](settings=settings),
            )
        )

    if settings.graph_db_uri:

        storage_flow = DBStorageUpdater(
            settings=settings,
            entity_type=entity_type,
        )

        db_handler = (
            FilmGraphHandler(settings=settings)
            if entity_type is Film
            else PersonGraphHandler(settings=settings)
        )

        tasks.append(
            storage_flow.execute.submit(
                input_storage=json_store,
                output_storage=db_handler,
            )
        )

    wait(tasks)
