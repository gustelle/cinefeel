import hashlib
from typing import Literal

from prefect import flow
from prefect.futures import wait

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.tasks.task_html_parsing import HtmlEntityExtractor
from src.settings import Settings


def hash_content(content: str) -> str:

    sha1 = hashlib.sha1()
    sha1.update(str.encode(content))
    return sha1.hexdigest()


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
    for content in html_store.scan():

        # compute a unique content_id for the content
        content_id = hash_content(content)

        tasks.append(
            analysis_flow.execute.submit(
                content_id=content_id,
                content=content,
                output_storage=json_store,
            )
        )

    wait(tasks)
