from typing import Literal

from prefect import flow
from prefect.futures import wait

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.tasks.task_html_parsing import HtmlEntityExtractor
from src.settings import Settings


@flow(
    name="extract_entities",
    description="Extract entities (Film or Person) from HTML contents",
)
def extract_entities_flow(
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

    analysis_flow = HtmlEntityExtractor(
        settings=settings,
        entity_type=entity_type,
    )

    html_store = RedisTextStorage(settings=settings)
    json_store = RedisJsonStorage[entity_type](settings=settings)

    # iterate over all HTML contents in Redis
    while content := html_store.scan():

        tasks.append(
            analysis_flow.execute.submit(
                content=content,
                output_storage=json_store,
            )
        )

    wait(tasks)
