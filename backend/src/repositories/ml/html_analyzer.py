import re

from loguru import logger

from src.entities.film import Film
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.entity_transformer import IEntityTransformer
from src.interfaces.link_extractor import IHtmlExtractor
from src.interfaces.similarity import ISimilaritySearch
from src.repositories.html_parser.html_semantic import HtmlSplitter, Section


class HtmlContentAnalyzer(IContentAnalyzer):

    entity_transformer: IEntityTransformer
    title_matcher: ISimilaritySearch
    html_splitter: HtmlSplitter
    html_extractor: IHtmlExtractor

    def __init__(
        self,
        entity_transformer: IEntityTransformer,
        title_matcher: ISimilaritySearch,
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
        self.title_matcher = title_matcher
        self.html_splitter = html_splitter
        self.html_extractor = html_extractor

    def _find_tech_spec(
        self,
        sections: list[Section],
    ) -> Section | None:

        most_similar_section = None

        for text_query in ["fiche technique", "synopsis", "résumé"]:

            most_similar_section_title = self.title_matcher.most_similar(
                query=text_query,
                corpus=[section.title for section in sections],
            )

            if most_similar_section_title is None:
                continue

            pattern = re.compile(rf"\s*{text_query}\s*", re.IGNORECASE)

            most_similar_sections = [
                section for section in sections if pattern.match(section.title)
            ]

            if len(most_similar_sections) == 0:
                logger.warning(
                    f"no section found for '{text_query}' (found '{most_similar_section_title}')"
                )
                continue

            most_similar_section = most_similar_sections[0]

            if (
                most_similar_section is None
                or most_similar_section.content is None
                or len(most_similar_section.content) == 0
            ):
                logger.warning(
                    f"content of section '{most_similar_section_title}' is empty"
                )
                continue

            break

        return most_similar_section

    def analyze(self, html_content: str) -> Film | None:
        """
        Analyzes the HTML content and extracts a film.
        """

        # split the HTML content into sections
        sections = self.html_splitter.split(html_content)

        if sections is None or len(sections) == 0:
            logger.warning("no sections found, skipping the content")
            return None

        tech_spec = self._find_tech_spec(
            sections=sections,
        )

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

            logger.debug(f"Using tech splec as context: '{ctx}'")

        resp = self.entity_transformer.to_entity(
            content=ctx,
        )

        logger.info(f"response : '{resp.model_dump_json()}'")

        return resp
