
from loguru import logger

from src.entities.film import Film
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.entity_transformer import IEntityTransformer
from src.interfaces.extractor import IHtmlExtractor
from src.interfaces.similarity import ISimilaritySearch
from src.repositories.html_parser.splitter import HtmlSplitter


class HtmlContentAnalyzer(IContentAnalyzer):

    entity_transformer: IEntityTransformer
    section_searcher: ISimilaritySearch
    html_splitter: HtmlSplitter
    html_extractor: IHtmlExtractor

    def __init__(
        self,
        entity_transformer: IEntityTransformer,
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
        self.entity_transformer = entity_transformer
        self.section_searcher = section_searcher
        self.html_splitter = html_splitter
        self.html_extractor = html_extractor

    def analyze(self, html_content: str) -> Film | None:
        """
        Analyzes the HTML content and extracts a film.
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

        resp = self.entity_transformer.to_entity(
            content=ctx,
        )

        logger.info(f"response : '{resp.model_dump_json()}'")

        return resp
