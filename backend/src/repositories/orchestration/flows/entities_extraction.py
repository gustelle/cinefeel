from typing import Literal

from prefect import flow
from prefect.futures import wait

from src.entities.movie import Movie
from src.entities.person import Person
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.nlp_processor import Processor
from src.interfaces.storage import IStorageHandler
from src.repositories.db.redis.json import RedisJsonStorage
from src.repositories.db.redis.text import RedisTextStorage
from src.repositories.orchestration.tasks.task_html_parsing import HtmlDataParserTask
from src.settings import Settings


@flow(
    name="extract_entities",
    description="Extract entities (Movie or Person) from HTML contents",
)
def extract_entities_flow(
    settings: Settings,
    entity_type: Literal["Movie", "Person"],
    page_id: str | None = None,
    # for testing purposes, we can inject a custom analyzer and section searcher
    entity_analyzer: IContentAnalyzer | None = None,
    section_searcher: Processor | None = None,
    html_store: IStorageHandler | None = None,
    json_store: IStorageHandler | None = None,
) -> None:
    """
    Extract entities (Movie or Person) from HTML contents

    for technical reasons (Prefect serialization) we use "Movie" and "Person" as entity_type
    but they map to the Movie and Person classes respectively.

    If page_id is provided, only that specific page will be processed. If not, all pages in the HTML storage will be processed.

    Args:
        settings (Settings): Application settings.
        entity_type (Literal["Movie", "Person"]): Type of entity to extract.
        page_id (str | None, optional): Specific page ID to process. Defaults to None (process all pages).
        entity_analyzer (IContentAnalyzer | None, optional): Custom entity analyzer
        section_searcher (Processor | None, optional): Custom section searcher
        html_store (IStorageHandler | None, optional): Custom HTML storage handler, defaults to `RedisTextStorage`
        json_store (IStorageHandler | None, optional): Custom JSON storage handler, defaults to `RedisJsonStorage`
    """

    tasks = []
    _ent_type = None

    match entity_type:
        case "Movie":
            _ent_type = Movie
        case "Person":
            _ent_type = Person
        case _:
            raise ValueError(f"Unsupported entity type: {entity_type}")

    parser_task = HtmlDataParserTask(
        settings=settings,
        entity_type=_ent_type,
        analyzer=entity_analyzer,
        search_processor=section_searcher,
    )

    html_store = html_store or RedisTextStorage(settings=settings)
    json_store = json_store or RedisJsonStorage[_ent_type](settings=settings)

    if page_id:
        content = html_store.select(content_id=page_id)
        if content:
            tasks.append(
                parser_task.execute.submit(
                    content=content,
                    output_storage=json_store,
                )
            )
        else:
            raise ValueError(f"No HTML content found for page_id: {page_id}")
    else:
        # iterate over all HTML contents in Redis
        for content_id, content in html_store.scan():
            tasks.append(
                parser_task.execute.submit(
                    content=content,
                    output_storage=json_store,
                )
            )
            break  # for testing, process only one

    wait(tasks)
