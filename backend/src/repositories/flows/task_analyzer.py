from typing import Type

import dask
import distributed
from prefect import flow, get_run_logger, task
from prefect.futures import PrefectFuture
from prefect_dask import DaskTaskRunner

from src.entities.film import Film
from src.entities.person import Person
from src.entities.storable import Storable
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.html_parser.html_analyzer import HtmlContentAnalyzer
from src.repositories.html_parser.html_splitter import HtmlSplitter
from src.repositories.html_parser.wikipedia_extractor import WikipediaExtractor
from src.repositories.ml.bert_similarity import SimilarSectionSearch
from src.repositories.ml.bert_summary import SectionSummarizer
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.repositories.ml.ollama_parser import OllamaParser
from src.repositories.storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings


class AnalysisFlow(ITaskExecutor):
    """
    handles persistence of `Film` or `Person` objects into JSON files.
    """

    entity_type: type[Film | Person]
    settings: Settings
    dask_client: distributed.Client
    dask_client_address: str

    def __init__(self, settings: Settings, entity_type: Type[Film | Person]):
        self.settings = settings
        self.entity_type = entity_type

    @task(task_run_name="do_analysis-{content_id}", timeout_seconds=120)
    def do_analysis(
        self, analyzer: IContentAnalyzer, content_id: str, html_content: str
    ) -> Storable | None:
        """
        Analyze the content and return a storable entity.

        Args:
            analyzer (IContentAnalyzer): _description_
            content_id (str): _description_
            html_content (str): _description_

        Returns:
            Storable | None: _description_
        """

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
        task_runner=DaskTaskRunner(
            cluster_kwargs={
                "n_workers": 4,
                "resources": {"GPU": 1, "process": 1},
                "dashboard_address": ":8787",
                "memory_limit": "4GB",
            }
        ),
    )
    def execute(
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
            with (
                dask.annotate(resources={"GPU": 1}),
                dask.config.set({"array.chunk-size": "512 MiB"}),
            ):
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
