import dask
import dask.distributed
from prefect import flow, get_run_logger, task
from prefect.futures import PrefectFuture
from prefect_dask import DaskTaskRunner

from src.entities.film import Film
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.storage import IStorageHandler
from src.repositories.html_parser.splitter import HtmlSplitter
from src.repositories.html_parser.wikipedia_extractor import WikipediaExtractor
from src.repositories.ml.bert_similarity import BertSimilaritySearch
from src.repositories.ml.html_analyzer import HtmlContentAnalyzer
from src.repositories.ml.ollama_parser import OllamaParser
from src.repositories.storage.html_storage import LocalTextStorage
from src.repositories.storage.json_storage import JSONFilmStorageHandler
from src.settings import Settings

client = dask.distributed.Client(
    n_workers=4,
    resources={"GPU": 1, "process": 1},
    dashboard_address=":8787",
    memory_limit="4GB",
)


@task(timeout_seconds=120)
def do_analysis(
    analyzer: IContentAnalyzer, content_id: str, html_content: str
) -> Film | None:
    """
    Submit tasks to the executor with a specified concurrency level.
    """
    logger = get_run_logger()
    logger.info(f"Analyzing content: '{content_id}'")

    return analyzer.analyze(content_id, html_content)


@task
def do_storage(film_storage: IStorageHandler, film: Film | None) -> None:
    """
    Store the film entity in the storage.
    """
    try:

        logger = get_run_logger()

        if film is not None and isinstance(film, Film):
            logger.info(f"Storing film: {film}")
            # store the film entity
            film_storage.insert(film.uid, film)
        else:
            logger = get_run_logger()
            logger.warning("skipping storage, film is None or not a Film instance.")

    except Exception as e:
        logger = get_run_logger()
        logger.error(f"Error storing film: {e}")
        raise e


@flow(task_runner=DaskTaskRunner(address=client.scheduler.address))
def analyze_films(
    settings: Settings,
    content_ids: list[str] | None = None,
) -> None:

    logger = get_run_logger()

    html_storage = LocalTextStorage[Film](
        path=settings.persistence_directory,
    )

    film_storage = JSONFilmStorageHandler(settings=settings)

    analyzer = HtmlContentAnalyzer[Film](
        content_parser=OllamaParser[Film](settings=settings),
        section_searcher=BertSimilaritySearch(settings=settings),
        html_splitter=HtmlSplitter(),
        html_extractor=WikipediaExtractor(),
    )

    i = 0

    # send concurrent tasks to analyze HTML content
    # don't wait for the task to be completed
    futures = []
    for content_id in content_ids:

        file_content = html_storage.select(content_id)

        if file_content is None:
            logger.warning(f"Content with ID '{content_id}' not found in storage.")
            continue

        # analyze the HTML content
        with dask.annotate(resources={"GPU": 1}), dask.config.set(
            {"array.chunk-size": "512 MiB"}
        ):
            future = do_analysis.submit(
                analyzer=analyzer,
                content_id=content_id,
                html_content=file_content,
            )

        futures.append(
            do_storage.submit(
                film_storage=film_storage,
                film=future,
            )
        )

        i += 1
        if i > 2:
            break

    # now wait for all tasks to complete
    future: PrefectFuture
    for future in futures:
        try:
            future.result(timeout=30, raise_on_failure=True)
        except TimeoutError:
            logger.warning(
                f"Task timed out for {future.task_run_id}, skipping storage."
            )
        except Exception as e:
            logger.error(f"Error in task execution: {e}")

    logger.info("'analyze_films' flow completed successfully.")
