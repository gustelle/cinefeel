from prefect import flow, get_run_logger, task
from prefect.futures import PrefectFuture

from src.entities.film import Film
from src.repositories.html_parser.splitter import HtmlSplitter
from src.repositories.html_parser.wikipedia_extractor import WikipediaExtractor
from src.repositories.ml.bert_similarity import BertSimilaritySearch
from src.repositories.ml.html_analyzer import HtmlContentAnalyzer
from src.repositories.ml.ollama_parser import OllamaTransformer
from src.repositories.storage.html_storage import LocalTextStorage
from src.repositories.storage.json_storage import JSONFilmStorageHandler
from src.settings import Settings

CONCURRENCY = 4


@task
def do_analysis(analyzer: HtmlContentAnalyzer, html_content: str) -> Film | None:
    """
    Submit tasks to the executor with a specified concurrency level.
    """
    return analyzer.analyze(html_content)


@task
def do_storage(
    film_storage: JSONFilmStorageHandler,
    future: PrefectFuture[Film | None],
) -> None:
    """
    Store the film entity in the storage.
    """
    result = future.result()
    film = result if isinstance(result, Film) else None

    if film is not None:
        # store the film entity
        film_storage.insert(film)
    else:
        logger = get_run_logger()
        logger.warning("Film is None, skipping storage.")


@flow()
def analyze_films(
    settings: Settings,
    content_ids: list[str] | None = None,
) -> None:
    """ """

    logger = get_run_logger()

    html_storage = LocalTextStorage[Film](
        path=settings.persistence_directory,
    )

    film_storage = JSONFilmStorageHandler(settings=settings)

    analyzer = HtmlContentAnalyzer(
        entity_transformer=OllamaTransformer[Film](settings=settings),
        section_searcher=BertSimilaritySearch(settings=settings),
        html_splitter=HtmlSplitter(),
        html_extractor=WikipediaExtractor(),
    )

    i = 0

    # iterate over the list of films
    for content_id in content_ids:
        for file_content in html_storage.scan(
            file_pattern=content_id,
        ):
            # analyze the HTML content
            future = do_analysis.submit(
                analyzer=analyzer,
                html_content=file_content,
            )

            do_storage.submit(
                film_storage=film_storage,
                future=future,
            )

        i += 1
        if i > 2:
            break

    logger.info("Flow completed successfully.")
