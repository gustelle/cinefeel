from typing import Type

import orjson
from prefect import get_run_logger, runtime, task

from src.entities.composable import Composable
from src.entities.content import UsualSectionTitles_FR_fr
from src.entities.movie import FilmActor, FilmSpecifications, FilmSummary, Movie
from src.entities.person import Biography, Person
from src.entities.woa import WOAInfluence
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.nlp_processor import Processor
from src.interfaces.resolver import ResolutionConfiguration
from src.interfaces.stats import IStatsCollector, StatKey
from src.interfaces.storage import IStorageHandler
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
from src.settings import MLSettings, SectionSettings


def do_analysis(
    content_id: str,
    html_content: str,
    section_settings: SectionSettings,
    ml_settings: MLSettings,
    entity_type: Type[Composable],
    analyzer: IContentAnalyzer,
    search_processor: Processor,
) -> Composable | None:
    """
    Analyze the content and return a storable entity.

    """
    logger = get_run_logger()

    result = analyzer.process(content_id, html_content)

    if result is None:
        logger.warning(
            f"No Sections or Composable found for content ID '{content_id}'."
        )
        return None

    base_info, sections = result

    logger.info(
        f"Extracted base info & {len(sections) if sections else 0} sections of a '{entity_type.__name__}' for content '{content_id}'"
    )

    # assemble the entity from the sections
    if entity_type == Movie:
        return MovieResolver(
            section_searcher=search_processor,
            section_settings=section_settings,
            ml_settings=ml_settings,
            configurations=[
                ResolutionConfiguration(
                    # extractor=MistralDataMiner(settings=self.settings),
                    extractor=GenericOllamaExtractor(settings=ml_settings),
                    section_titles=[
                        UsualSectionTitles_FR_fr.INFOBOX,
                        UsualSectionTitles_FR_fr.TECHNICAL_SHEET,
                    ],
                    extracted_type=FilmSpecifications,
                ),
                ResolutionConfiguration(
                    extractor=GenericOllamaExtractor(settings=ml_settings),
                    # extractor=MistralDataMiner(settings=self.settings),
                    section_titles=[UsualSectionTitles_FR_fr.DISTRIBUTION],
                    extracted_type=FilmActor,
                ),
                ResolutionConfiguration(
                    extractor=GenericOllamaExtractor(settings=ml_settings),
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
                    extractor=InfluenceOllamaExtractor(settings=ml_settings),
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
    elif entity_type == Person:
        return PersonResolver(
            section_searcher=search_processor,
            ml_settings=ml_settings,
            section_settings=section_settings,
            configurations=[
                ResolutionConfiguration(
                    extractor=GenericOllamaExtractor(settings=ml_settings),
                    # extractor=MistralDataMiner(settings=self.settings),
                    section_titles=[
                        UsualSectionTitles_FR_fr.BIOGRAPHY,
                        UsualSectionTitles_FR_fr.INFOBOX,
                    ],
                    extracted_type=Biography,
                ),
                ResolutionConfiguration(
                    extractor=InfluenceOllamaExtractor(settings=ml_settings),
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
        logger.error(f"Unsupported entity type '{entity_type.__name__}' for analysis.")
        return None


@task(
    task_run_name="html-to-entity-{content_id}",
    log_prints=False,
)
def execute_task(
    content_id: str,
    content: str,
    ml_settings: MLSettings,
    section_settings: SectionSettings,
    entity_type: Type[Composable],
    output_storage: IStorageHandler[Composable],
    # for testing,
    # enable injection of dependencies
    analyzer: IContentAnalyzer = None,
    search_processor: Processor = None,
    stats_collector: IStatsCollector = None,
) -> None:

    flow_id = runtime.flow_run.id

    try:

        logger = get_run_logger()

        analyzer = analyzer or Html2TextSectionsChopper(
            content_splitter=WikipediaAPIContentSplitter(
                parser=WikipediaParser(),
                pruner=HTMLSimplifier(),
                settings=section_settings,
            ),
            post_processors=[
                TextSectionConverter(),
                SectionSummarizer(settings=ml_settings),
            ],
        )

        search_processor = search_processor or SimilarSectionSearch(
            settings=ml_settings
        )

        entity = do_analysis(
            content_id=content_id,
            html_content=content,
            section_settings=section_settings,
            ml_settings=ml_settings,
            entity_type=entity_type,
            analyzer=analyzer,
            search_processor=search_processor,
        )

        if entity is not None:
            stats_collector.inc_value(StatKey.EXTRACTION_SUCCESS, flow_id=flow_id)
            output_storage.insert_many(
                [entity],
            )
        else:
            if stats_collector:
                stats_collector.inc_value(StatKey.EXTRACTION_VOID, flow_id=flow_id)

    except Exception:

        # track extraction failure
        if stats_collector:
            stats_collector.inc_value(StatKey.EXTRACTION_FAILED, flow_id=flow_id)

        # re-raise for Prefect to handle retries if needed
        raise

    finally:
        if stats_collector:
            logger.info(
                orjson.dumps(
                    stats_collector.collect(flow_id=flow_id), option=orjson.OPT_INDENT_2
                ).decode()
            )
