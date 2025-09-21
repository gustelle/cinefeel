import hashlib
from typing import Type

from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import wait

from src.entities.composable import Composable
from src.entities.movie import FilmActor, FilmSpecifications, FilmSummary, Movie
from src.entities.person import (
    Biography,
    ChildHoodConditions,
    Person,
    PersonCharacteristics,
    PersonVisibleFeatures,
)
from src.entities.woa import WOAInfluence
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.nlp_processor import Processor
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
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.repositories.ml.html_to_text import TextSectionConverter
from src.repositories.ml.ollama_childhood import ChildhoodOllamaExtractor
from src.repositories.ml.ollama_generic import GenericOllamaExtractor
from src.repositories.ml.ollama_influences import InfluenceOllamaExtractor
from src.repositories.ml.ollama_person_feats import PersonFeaturesOllamaExtractor
from src.repositories.ml.ollama_person_visualizer import PersonOllamaVisualAnalysis
from src.repositories.ml.similarity import SimilarSectionSearch
from src.repositories.ml.summary import SectionSummarizer
from src.repositories.resolver.movie_resolver import MovieResolver
from src.repositories.resolver.person_resolver import PersonResolver
from src.settings import Settings


class HtmlEntityExtractor(ITaskExecutor):
    """
    Analyses the HTML content from an input_storage
    and creates eventually a Composable entity stored in the output_storage.
    """

    entity_type: type[Composable]
    settings: Settings
    analyzer: IContentAnalyzer
    search_processor: SimilarSectionSearch

    def __init__(
        self,
        settings: Settings,
        entity_type: Type[Composable],
        # for testing,
        # enable injection of dependencies
        analyzer: IContentAnalyzer = None,
        search_processor: Processor = None,
    ):
        self.settings = settings
        self.entity_type = entity_type

        self.analyzer = analyzer or Html2TextSectionsChopper(
            content_splitter=WikipediaAPIContentSplitter(
                parser=WikipediaParser(),
                pruner=HTMLSimplifier(),
                settings=self.settings,
            ),
            post_processors=[
                TextSectionConverter(),
                SectionSummarizer(settings=self.settings),
            ],
        )

        self.search_processor = search_processor or SimilarSectionSearch(
            settings=self.settings
        )

    @task(task_run_name="do_analysis-{content_id}", cache_policy=NO_CACHE)
    def do_analysis(
        self,
        content_id: str,
        html_content: str,
    ) -> Composable | None:
        """
        Analyze the content and return a storable entity.

        """
        logger = get_run_logger()
        result = self.analyzer.process(content_id, html_content)

        if result is None:
            logger.warning(
                f"No Sections or Composable found for content ID '{content_id}'."
            )
            return None

        base_info, sections = result

        logger.info(
            f"Extracting '{self.entity_type.__name__}' for content '{str(base_info.permalink)}'"
        )

        # assemble the entity from the sections
        if self.entity_type == Movie:
            return MovieResolver(
                settings=self.settings,
                section_searcher=self.search_processor,
                configurations=[
                    ResolutionConfiguration(
                        # extractor=MistralDataMiner(settings=self.settings),
                        extractor=GenericOllamaExtractor(settings=self.settings),
                        section_titles=[INFOBOX_SECTION_TITLE, "Fiche technique"],
                        extracted_type=FilmSpecifications,
                    ),
                    ResolutionConfiguration(
                        extractor=GenericOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
                        section_titles=["Distribution"],
                        extracted_type=FilmActor,
                    ),
                    ResolutionConfiguration(
                        extractor=GenericOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            "Synopsis",
                            "Résumé",
                            ORPHAN_SECTION_TITLE,
                        ],
                        extracted_type=FilmSummary,
                    ),
                    # search for influences
                    ResolutionConfiguration(
                        extractor=InfluenceOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
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
            return PersonResolver(
                settings=self.settings,
                section_searcher=self.search_processor,
                configurations=[
                    ResolutionConfiguration(
                        extractor=GenericOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            INFOBOX_SECTION_TITLE,
                        ],
                        extracted_type=Biography,
                    ),
                    ResolutionConfiguration(
                        extractor=ChildhoodOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
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
                        extractor=PersonFeaturesOllamaExtractor(settings=self.settings),
                        section_titles=[
                            ORPHAN_SECTION_TITLE,
                            "Biographie",
                        ],
                        extracted_type=PersonCharacteristics,
                    ),
                    ResolutionConfiguration(
                        extractor=PersonOllamaVisualAnalysis(settings=self.settings),
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

    @task(task_run_name="to_storage-{entity.uid}", cache_policy=NO_CACHE)
    def to_storage(self, storage: IStorageHandler, entity: Composable) -> None:
        """
        Store the film entity in the storage.
        """

        if entity is not None:
            storage.insert_many(
                [entity],
            )

    def compute_uid(self, content: str) -> str:
        sha1 = hashlib.sha1()
        sha1.update(str.encode(content))
        return sha1.hexdigest()

    @task(
        cache_policy=NO_CACHE, retries=3, retry_delay_seconds=5, tags=["cinefeel_tasks"]
    )
    def execute(
        self,
        content: str,
        output_storage: IStorageHandler[Composable],
    ) -> None:

        # need to keep track of the futures to wait for them later
        # see: https://github.com/PrefectHQ/prefect/issues/17517
        _futures = []

        content_id = self.compute_uid(content)

        future_entity = self.do_analysis.submit(
            content_id=content_id,
            html_content=content,
        )

        _futures.append(
            self.to_storage.submit(
                storage=output_storage,
                entity=future_entity,
            )
        )

        wait(_futures)
