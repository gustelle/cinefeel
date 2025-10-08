from typing import Type

from prefect import get_run_logger, task

from src.entities.composable import Composable
from src.entities.content import UsualSectionTitles_FR_fr
from src.entities.movie import FilmActor, FilmSpecifications, FilmSummary, Movie
from src.entities.person import Biography, Person
from src.entities.woa import WOAInfluence
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.nlp_processor import Processor
from src.interfaces.resolver import ResolutionConfiguration
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.html_parser.html_chopper import Html2TextSectionsChopper
from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.repositories.ml.html_to_text import TextSectionConverter
from src.repositories.ml.ollama_generic import GenericOllamaExtractor
from src.repositories.ml.ollama_influences import InfluenceOllamaExtractor
from src.repositories.ml.similarity import SimilarSectionSearch
from src.repositories.ml.summary import SectionSummarizer
from src.repositories.resolver.movie_resolver import MovieResolver
from src.repositories.resolver.person_resolver import PersonResolver
from src.settings import Settings


class HtmlDataParserTask(ITaskExecutor):
    """
    The objective of this task is to parse raw HTML content
    and extract structured entities like Movies or Persons.

    * It relies on a `IContentAnalyzer` to process the HTML which extracts relevant information and structures it into a `Composable` entity.
    * A `Processor` is used to facilitate searching for relevant sections within the HTML content to extract specific details.
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

    @task(
        task_run_name="do_analysis-{content_id}",
    )
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
            f"Extracted base info & {len(sections) if sections else 0} sections of a '{self.entity_type.__name__}' for content '{content_id}'"
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
                        section_titles=[
                            UsualSectionTitles_FR_fr.INFOBOX,
                            UsualSectionTitles_FR_fr.TECHNICAL_SHEET,
                        ],
                        extracted_type=FilmSpecifications,
                    ),
                    ResolutionConfiguration(
                        extractor=GenericOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[UsualSectionTitles_FR_fr.DISTRIBUTION],
                        extracted_type=FilmActor,
                    ),
                    ResolutionConfiguration(
                        extractor=GenericOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            UsualSectionTitles_FR_fr.SYNOPSIS,
                            UsualSectionTitles_FR_fr.SUMMARY,
                            UsualSectionTitles_FR_fr.NO_TITLE,
                        ],
                        extracted_type=FilmSummary,
                    ),
                    # search for influences
                    ResolutionConfiguration(
                        extractor=InfluenceOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            UsualSectionTitles_FR_fr.CONTEXT,
                            UsualSectionTitles_FR_fr.ANALYSIS,
                            UsualSectionTitles_FR_fr.INFLUENCES,
                            UsualSectionTitles_FR_fr.NO_TITLE,
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
                            UsualSectionTitles_FR_fr.BIOGRAPHY,
                            UsualSectionTitles_FR_fr.INFOBOX,
                        ],
                        extracted_type=Biography,
                    ),
                    ResolutionConfiguration(
                        extractor=InfluenceOllamaExtractor(settings=self.settings),
                        # extractor=MistralDataMiner(settings=self.settings),
                        section_titles=[
                            UsualSectionTitles_FR_fr.BIOGRAPHY,
                            UsualSectionTitles_FR_fr.INFLUENCES,
                            UsualSectionTitles_FR_fr.NO_TITLE,
                        ],
                        extracted_type=WOAInfluence,
                    ),
                    # ResolutionConfiguration(
                    #     extractor=ChildhoodOllamaExtractor(settings=self.settings),
                    #     # extractor=MistralDataMiner(settings=self.settings),
                    #     section_titles=[
                    #         "Biographie",
                    #     ],
                    #     extracted_type=ChildHoodConditions,
                    # ),
                    # search for influences
                    # ResolutionConfiguration(
                    #     extractor=InfluenceExtractor(settings=self.settings),
                    #     section_titles=[
                    #         "Biographie",
                    #         "Influences",
                    #     ],
                    #     extracted_type=PersonInfluence,
                    # ),
                    # ResolutionConfiguration(
                    #     extractor=PersonFeaturesOllamaExtractor(settings=self.settings),
                    #     section_titles=[
                    #         ORPHAN_SECTION_TITLE,
                    #         "Biographie",
                    #     ],
                    #     extracted_type=PersonCharacteristics,
                    # ),
                    # ResolutionConfiguration(
                    #     extractor=PersonOllamaVisualAnalysis(settings=self.settings),
                    #     section_titles=[INFOBOX_SECTION_TITLE],
                    #     extracted_type=PersonVisibleFeatures,
                    #     # must specify the parent type
                    #     # for the resolution to work correctly
                    #     # because PersonVisibleFeatures is not a direct child of Person
                    #     resolve_as=PersonCharacteristics,
                    # ),
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
        task_run_name="to_storage-{entity.uid}",
    )
    def to_storage(self, storage: IStorageHandler, entity: Composable) -> None:
        """
        Store the film entity in the storage.
        """

        if entity is not None:
            storage.insert_many(
                [entity],
            )

    @task(
        task_run_name="html_parsing_mother-{content_id}",
    )
    def execute(
        self,
        content_id: str,
        content: str,
        output_storage: IStorageHandler[Composable],
    ) -> None:

        try:

            entity_fut = self.do_analysis.with_options(
                cache_key_fn=lambda *_: f"do_analysis-{content_id}",
            ).submit(
                content_id=content_id,
                html_content=content,
            )

            self.to_storage.with_options(
                cache_key_fn=lambda *_: f"to_storage-{content_id}",
            ).submit(storage=output_storage, entity=entity_fut).wait()

        except Exception as e:
            logger = get_run_logger()
            logger.error(f"Error storing entity for content ID '{content_id}': {e}")
