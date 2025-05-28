from typing import Type

from prefect import flow, get_run_logger, task
from prefect.futures import PrefectFuture
from prefect_dask import DaskTaskRunner

from src.entities.film import Film
from src.entities.person import Person
from src.entities.storable import Storable
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.storage import IStorageHandler
from src.repositories.html_parser.html_analyzer import HtmlContentAnalyzer
from src.repositories.html_parser.html_splitter import HtmlSplitter
from src.repositories.html_parser.wikipedia_extractor import WikipediaExtractor
from src.repositories.ml.bert_similarity import SimilarSectionSearch
from src.repositories.ml.bert_summary import SectionSummarizer
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.repositories.ml.ollama_parser import OllamaParser
from src.repositories.storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings

# TODO: externalize the Dask client configuration to settings
# client = dask.distributed.Client(
#     n_workers=4,
#     resources={"GPU": 1, "process": 1},
#     dashboard_address=":8787",
#     memory_limit="4GB",
# )


class AnalysisFlowRunner:
    """
    handles persistence of `Film` or `Person` objects into JSON files.
    """

    entity_type: type[Film | Person]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: Type[Film | Person]):
        self.settings = settings
        self.entity_type = entity_type

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type

        return new_cls

    @task(task_run_name="do_analysis-{content_id}", timeout_seconds=120)
    def do_analysis(
        self, analyzer: IContentAnalyzer, content_id: str, html_content: str
    ) -> Storable | None:
        """
        Submit tasks to the executor with a specified concurrency level.
        """
        logger = get_run_logger()
        logger.info(f"Analyzing content: '{content_id}'")

        return analyzer.analyze(content_id, html_content)

    @task(
        task_run_name="store_entity-{entity}",
    )
    def store(self, storage: IStorageHandler, entity: Storable) -> None:
        """
        Store the film entity in the storage.
        """

        logger = get_run_logger()

        if entity is not None:
            storage.insert(entity.uid, entity)
        else:
            logger.warning("skipping storage, entity is None")

    @flow(
        name="analyze",
        task_runner=DaskTaskRunner(),  # address=client.scheduler.address),
    )
    def analyze(
        self,
        content_ids: list[str] | None,
        storage_handler: IStorageHandler,
    ) -> None:

        logger = get_run_logger()

        person_storage = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        analyzer = HtmlContentAnalyzer[self.entity_type](
            content_parser=OllamaParser[self.entity_type](settings=self.settings),
            section_searcher=SimilarSectionSearch(settings=self.settings),
            html_splitter=HtmlSplitter(),
            html_extractor=WikipediaExtractor(),
            html_simplifier=HTMLSimplifier(),
            summarizer=SectionSummarizer(settings=self.settings),
        )

        i = 0

        # send concurrent tasks to analyze HTML content
        # don't wait for the task to be completed
        storage_futures = []

        # need to keep track of the futures to wait for them later
        # see: https://github.com/PrefectHQ/prefect/issues/17517
        analysis_futures = []

        for content_id in content_ids:

            file_content = storage_handler.select(content_id)

            if file_content is None:
                logger.warning(f"Content with ID '{content_id}' not found in storage.")
                continue

            # analyze the HTML content
            # with (
            #     dask.annotate(resources={"GPU": 1}),
            #     dask.config.set({"array.chunk-size": "512 MiB"}),
            # ):
            future = self.do_analysis.submit(
                analyzer=analyzer,
                content_id=content_id,
                html_content=file_content,
            )
            analysis_futures.append(future)

            storage_futures.append(
                self.store.submit(
                    storage=person_storage,
                    entity=future,
                )
            )

            i += 1
            if i > 2:
                break

        # now wait for all tasks to complete
        future: PrefectFuture
        for future in storage_futures:
            try:
                future.result(timeout=60, raise_on_failure=True)
            except TimeoutError:
                logger.warning(
                    f"Task timed out for {future.task_run_id}, skipping storage."
                )
            except Exception as e:
                logger.error(f"Error in task execution: {e}")

        logger.info("'analyze_persons' flow completed successfully.")
