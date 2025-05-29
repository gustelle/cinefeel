from loguru import logger

from src.entities.content import Section
from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.content_parser import IContentParser
from src.interfaces.extractor import IHtmlExtractor
from src.interfaces.similarity import MLProcessor
from src.repositories.html_parser.html_splitter import HtmlSplitter


class HtmlContentAnalyzer[T: Film | Person](IContentAnalyzer[T]):

    content_parser: IContentParser
    section_searcher: MLProcessor
    summarizer: MLProcessor
    html_splitter: HtmlSplitter
    html_simplifier: MLProcessor
    html_extractor: IHtmlExtractor
    entity_type: type[T]

    def __init__(
        self,
        content_parser: IContentParser,
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

        queries = []

        if self.entity_type is Film:
            queries = ["fiche technique", "synopsis", "résumé"]
        elif self.entity_type is Person:
            queries = ["biographie"]
        else:
            logger.error(
                f"Unsupported entity type: {self.entity_type}. "
                "Only Film and Person are supported."
            )
            return None

        for text_query in queries:

            tech_spec: Section = self.section_searcher.process(
                title=text_query,
                sections=sections,
            )

            if tech_spec is not None:
                # summarize the section if it is too long
                tech_spec = self.summarizer.process(tech_spec)
                break

        if tech_spec is None or tech_spec.content is None:

            info_table = self.html_extractor.retrieve_infoboxes(html_content)

            if info_table is None or len(info_table) == 0:
                logger.warning(
                    f"no info table found, skipping analysis of the content '{content_id}'"
                )
                return None

            # convert the DataFrame to a string
            ctx = "\n".join([f"{row.title}: {row.content}" for row in info_table])

            logger.debug(f"Using info table as context for content '{content_id}'")

        else:
            logger.debug(
                f"Using section '{tech_spec.title}' as context for content '{content_id}'"
            )
            ctx = tech_spec.content

        resp: T = self.content_parser.resolve(
            content=ctx,
        )

        if resp is None:
            logger.warning("no entity found, skipping the content")
            return None

        # set the content ID to the entity
        resp.uid = content_id

        logger.info(f"response : '{resp.model_dump_json()}'")

        return resp
