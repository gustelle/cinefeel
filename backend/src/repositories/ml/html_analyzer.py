from loguru import logger

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.content_parser import IContentParser
from src.interfaces.extractor import IHtmlExtractor
from src.interfaces.similarity import ISimilaritySearch
from src.repositories.html_parser.splitter import HtmlSplitter


class HtmlContentAnalyzer[T: Film | Person](IContentAnalyzer[T]):

    content_parser: IContentParser
    section_searcher: ISimilaritySearch
    html_splitter: HtmlSplitter
    html_extractor: IHtmlExtractor
    entity_type: type[T] = Film

    def __init__(
        self,
        content_parser: IContentParser,
        section_searcher: ISimilaritySearch,
        html_splitter: HtmlSplitter,
        html_extractor: IHtmlExtractor,
    ):
        """
        Initializes the HtmlAnalyzer with a ChromaDB client.

        Args:
            client (chromadb.Client, optional): A ChromaDB client instance.
                Defaults to None, which creates an ephemeral client.
        """
        self.content_parser = content_parser
        self.section_searcher = section_searcher
        self.html_splitter = html_splitter
        self.html_extractor = html_extractor

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

        # split the HTML content into sections
        sections = self.html_splitter.split(html_content)

        if sections is None or len(sections) == 0:
            logger.warning("no sections found, skipping the content")
            return None

        for text_query in ["fiche technique", "synopsis", "résumé"]:

            tech_spec = self.section_searcher.most_similar_section(
                title=text_query,
                sections=sections,
            )

            if tech_spec is not None:
                break

        if tech_spec is None or tech_spec.content is None:

            info_table = self.html_extractor.retrieve_infoboxes(html_content)

            if info_table is None or len(info_table) == 0:
                logger.warning("no info table found, skipping the content")
                return None

            # convert the DataFrame to a string
            ctx = "\n".join([f"{row.title}: {row.content}" for row in info_table])

            logger.debug(f"Using info table as context: '{ctx}'")

        else:
            ctx = tech_spec.content

        resp: T = self.content_parser.resolve(
            content=ctx,
        )

        if resp is None:
            logger.warning("no entity found, skipping the content")
            return None

        # set the content ID to the entity
        resp.woa_id = content_id

        logger.info(f"response : '{resp.model_dump_json()}'")

        return resp
