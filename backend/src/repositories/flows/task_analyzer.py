from prefect import flow, get_run_logger

from src.entities.film import Film
from src.repositories.ml.html_analyzer import HtmlContentAnalyzer
from src.repositories.storage.html_storage import HtmlContentStorageHandler
from src.repositories.storage.json_storage import JSONFilmStorageHandler
from src.settings import Settings

CONCURRENCY = 4


@flow()
def analyze_films(
    settings: Settings,
) -> None:
    """
    TODO:

    Refactor using tasks
    """

    logger = get_run_logger()

    html_storage = HtmlContentStorageHandler[Film](
        path=settings.persistence_directory,
    )

    film_storage = JSONFilmStorageHandler(settings=settings)

    analyzer = HtmlContentAnalyzer()

    i = 0

    # iterate over the list of films
    for html_content in html_storage.scan():
        # analyze the HTML content

        film = analyzer.analyze(html_content)

        if film is not None:
            # store the film entity
            film_storage.insert(film.uid, film.model_dump(mode="json"))

        i += 1
        if i > 2:
            break

    logger.info("Flow completed successfully.")
