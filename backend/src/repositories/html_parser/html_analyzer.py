from loguru import logger

from src.entities.content import Section
from src.entities.film import (
    Film,
    FilmActor,
    FilmAssembler,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.entities.person import Person
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.content_parser import IContentExtractor
from src.interfaces.extractor import IHtmlExtractor
from src.interfaces.similarity import MLProcessor
from src.repositories.html_parser.html_splitter import HtmlSplitter


class HtmlContentAnalyzer[T: Film | Person](IContentAnalyzer[T]):

    content_parser: IContentExtractor
    section_searcher: MLProcessor
    summarizer: MLProcessor
    html_splitter: HtmlSplitter
    html_simplifier: MLProcessor
    html_extractor: IHtmlExtractor
    entity_type: type[T]

    def __init__(
        self,
        content_parser: IContentExtractor,
        html_simplifier: MLProcessor,
        section_searcher: MLProcessor,
        summarizer: MLProcessor,
        html_splitter: HtmlSplitter,
        html_extractor: IHtmlExtractor,
    ):
        """
        Initializes the HtmlAnalyzer with a ChromaDB client.

        Args:
            content_parser (IContentParser): The content parser to resolve the HTML content into an entity.
            html_simplifier (MLProcessor): The processor to simplify the HTML content.
            section_searcher (MLProcessor): The processor to search for sections in the HTML content.
            summarizer (MLProcessor): The processor to summarize sections if they are too long.
            html_splitter (HtmlSplitter): The splitter to divide the HTML content into sections.
            html_extractor (IHtmlExtractor): The extractor to retrieve infoboxes from the HTML content.
        """
        self.content_parser = content_parser
        self.section_searcher = section_searcher
        self.html_splitter = html_splitter
        self.html_extractor = html_extractor
        self.summarizer = summarizer
        self.html_simplifier = html_simplifier

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type

        return new_cls

    def analyze(self, content_id: str, html_content: str) -> T | None:
        """
        Analyzes the HTML content and resolves it into an entity of type T.

        TODO:
            - tests
            - catch exceptions when parsing the content

        Args:
            content_id (str): The unique identifier for the content being analyzed.
            html_content (str): The HTML content to analyze.

        Returns:
            Film | Person | None: An entity of type T containing the parsed data,
            or None if the parsing fails or the content is not relevant.
        """

        if not hasattr(self, "entity_type"):
            raise ValueError(
                "Entity type is not set. Please use the class with a specific entity type."
            )

        if html_content is None or len(html_content) == 0:
            logger.warning(f"no HTML content found for content '{content_id}'")
            return None

        # simplify the HTML content
        html_content = self.html_simplifier.process(html_content)

        # split the HTML content into sections
        sections = self.html_splitter.split(html_content)

        if sections is None or len(sections) == 0:
            logger.warning(f"no sections found, skipping the content '{content_id}'")
            return None

        # summarize the sections if they are too long
        sections = [
            self.summarizer.process(section) for section in sections if section.content
        ]

        additional_sections = self.html_extractor.retrieve_infoboxes(html_content)

        if additional_sections is not None and len(additional_sections) > 0:
            sections.extend(additional_sections)

        _entity_to_sections = {
            FilmMedia: ["Données clés", "Fragments"],
            FilmSpecifications: ["Fiche technique"],
            FilmActor: ["Distribution"],
            FilmSummary: ["Synopsis", "Résumé"],
        }

        parts = []

        for entity_type, titles in _entity_to_sections.items():
            for title in titles:
                section: Section = self.section_searcher.process(
                    title=title,
                    sections=sections,
                )
                if section is not None:

                    section_entity = self.content_parser.resolve(
                        content=section.content,
                        entity_type=entity_type,
                    )

                    if section_entity is None:
                        continue

                    logger.info(
                        f"Found a '{section_entity.__class__.__name__}' in '{section.title}' for content '{content_id}'."
                    )
                    parts.append(section_entity)

        if len(parts) == 0:
            logger.warning(
                f"No relevant sections found for content '{content_id}', skipping analysis."
            )
            return None

        return FilmAssembler().assemble(
            title=self.html_extractor.retrieve_title(html_content),
            uid=content_id,
            parts=parts,
        )
