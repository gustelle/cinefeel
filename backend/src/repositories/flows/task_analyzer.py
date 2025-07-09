from typing import Type

import dask
from prefect import flow, get_run_logger, task
from prefect.futures import PrefectFuture
from prefect_dask import DaskTaskRunner

from src.entities.composable import Composable
from src.entities.film import Film, FilmActor, FilmSpecifications, FilmSummary
from src.entities.person import (
    Biography,
    ChildHoodConditions,
    Person,
    PersonCharacteristics,
    PersonVisibleFeatures,
)
from src.entities.woa import WOAInfluence
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.resolver import ResolutionConfiguration
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.html_parser.html_chopper import Html2TextSectionsChopper
from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
from src.repositories.html_parser.wikipedia_info_retriever import (
    INFOBOX_SECTION_TITLE,
    ORPHAN_SECTION_TITLE,
    WikipediaParser,
)
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.repositories.ml.bert_similarity import SimilarSectionSearch
from src.repositories.ml.bert_summary import SectionSummarizer
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.repositories.ml.html_to_text import TextSectionConverter
from src.repositories.ml.mistral_data_miner import MistralDataMiner
from src.repositories.ml.ollama_person_feats import PersonFeaturesExtractor
from src.repositories.ml.ollama_person_visualizer import PersonVisualAnalysis
from src.repositories.resolver.film_resolver import BasicFilmResolver
from src.repositories.resolver.person_resolver import BasicPersonResolver
from src.settings import Settings


class AnalysisFlow(ITaskExecutor):
    """
    handles persistence of `Film` or `Person` objects into JSON files.

    """

    entity_type: type[Composable]
    settings: Settings

    def __init__(self, settings: Settings, entity_type: Type[Composable]):
        self.settings = settings
        self.entity_type = entity_type

    @task(task_run_name="do_analysis-{content_id}")
    def do_analysis(
        self, analyzer: IContentAnalyzer, content_id: str, html_content: str
    ) -> Composable | None:
        """
        Analyze the content and return a storable entity.

        Args:
            analyzer (IContentAnalyzer): _description_
            content_id (str): _description_
            html_content (str): _description_

        Returns:
            Storable | None: _description_
        """
        logger = get_run_logger()
        result = analyzer.process(content_id, html_content)

        if result is None:
            logger.warning(
                f"No Sections or Composable found for content ID '{content_id}'."
            )
            return None

        base_info, sections = result

        # assemble the entity from the sections
        if self.entity_type == Film:
            return BasicFilmResolver(
                section_searcher=SimilarSectionSearch(settings=self.settings),
                configurations=[
                    ResolutionConfiguration(
                        extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[INFOBOX_SECTION_TITLE, "Fiche technique"],
                        extracted_type=FilmSpecifications,
                    ),
                    ResolutionConfiguration(
                        # extractor=GenericInfoExtractor(settings=self.settings),
                        extractor=MistralDataMiner(settings=self.settings),
                        section_titles=["Distribution"],
                        extracted_type=FilmActor,
                    ),
                    ResolutionConfiguration(
                        # extractor=GenericInfoExtractor(settings=self.settings),
                        extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            "Synopsis",
                            "Résumé",
                            ORPHAN_SECTION_TITLE,
                        ],
                        extracted_type=FilmSummary,
                    ),
                    # search for influences
                    ResolutionConfiguration(
                        # extractor=InfluenceExtractor(settings=self.settings),
                        extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            "Contexte",
                            "Analyse",
                            "Influences",
                            ORPHAN_SECTION_TITLE,
                        ],
                        extracted_type=WOAInfluence,
                    ),
                ],
            ).resolve(
                base_info=base_info,
                sections=sections,
            )
        elif self.entity_type == Person:
            return BasicPersonResolver(
                section_searcher=SimilarSectionSearch(settings=self.settings),
                configurations=[
                    ResolutionConfiguration(
                        # extractor=GenericInfoExtractor(settings=self.settings),
                        extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            INFOBOX_SECTION_TITLE,
                        ],
                        extracted_type=Biography,
                    ),
                    ResolutionConfiguration(
                        # extractor=ChildhoodExtractor(settings=self.settings),
                        extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            "Biographie",
                        ],
                        extracted_type=ChildHoodConditions,
                    ),
                    # search for influences
                    # ResolutionConfiguration(
                    #     extractor=InfluenceExtractor(settings=self.settings),
                    #     section_titles=[
                    #         "Biographie",
                    #         "Influences",
                    #     ],
                    #     extracted_type=PersonInfluence,
                    # ),
                    ResolutionConfiguration(
                        extractor=PersonFeaturesExtractor(settings=self.settings),
                        section_titles=[
                            ORPHAN_SECTION_TITLE,
                            "Biographie",
                        ],
                        extracted_type=PersonCharacteristics,
                    ),
                    ResolutionConfiguration(
                        extractor=PersonVisualAnalysis(settings=self.settings),
                        section_titles=[INFOBOX_SECTION_TITLE],
                        extracted_type=PersonVisibleFeatures,
                        # must specify the parent type
                        # for the resolution to work correctly
                        # because PersonVisibleFeatures is not a direct child of Person
                        resolve_as=PersonCharacteristics,
                    ),
                ],
            ).resolve(
                base_info=base_info,
                sections=sections,
            )
        else:
            logger.error(
                f"Unsupported entity type '{self.entity_type.__name__}' for analysis."
            )
            return None

    @task(
        task_run_name="store_entity-{entity.uid}",
    )
    def store(self, storage: IStorageHandler, entity: Composable) -> None:
        """
        Store the film entity in the storage.
        """

        if entity is not None:
            storage.insert(entity.uid, entity)

    @flow(
        name="analyze",
        task_runner=DaskTaskRunner(
            cluster_kwargs={
                "n_workers": 4,
                "resources": {"GPU": 1, "process": 1},
                "dashboard_address": ":8787",
                "memory_limit": "4GB",
            },
        ),
    )
    def execute(
        self,
        content_ids: list[str] | None,
        storage_handler: IStorageHandler,
    ) -> None:

        logger = get_run_logger()

        json_p_storage = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        analyzer = Html2TextSectionsChopper(
            content_splitter=WikipediaAPIContentSplitter(
                parser=WikipediaParser(),
                pruner=HTMLSimplifier(),
            ),
            post_processors=[
                TextSectionConverter(),
                SectionSummarizer(settings=self.settings),
            ],
        )

        i = 0

        # send concurrent tasks to analyze HTML content
        # don't wait for the task to be completed
        storage_futures = []

        # need to keep track of the futures to wait for them later
        # see: https://github.com/PrefectHQ/prefect/issues/17517
        person_futures = []

        # analyze the HTML content
        with (
            dask.annotate(resources={"GPU": 1}),
            dask.config.set({"array.chunk-size": "512 MiB"}),
        ):

            for content_id in content_ids:

                file_content = storage_handler.select(content_id)

                if file_content is None:
                    logger.warning(
                        f"Content with ID '{content_id}' not found in storage."
                    )
                    continue

                future_person = self.do_analysis.submit(
                    analyzer=analyzer,
                    content_id=content_id,
                    html_content=file_content,
                )
                person_futures.append(future_person)

                storage_futures.append(
                    self.store.submit(
                        storage=json_p_storage,
                        entity=future_person,
                    )
                )

                i += 1
                if i > 1:
                    break

            # now wait for all tasks to complete
            future_storage: PrefectFuture
            for future_storage in storage_futures:
                try:
                    future_storage.result(
                        raise_on_failure=True, timeout=self.settings.task_timeout
                    )
                except TimeoutError:
                    logger.warning(
                        f"Task timed out for {future_storage.task_run_id}, skipping storage."
                    )
                except Exception as e:
                    logger.error(f"Error in task execution: {e}")

        logger.info("'analyze' flow completed successfully.")
