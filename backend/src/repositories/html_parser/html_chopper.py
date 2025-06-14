from loguru import logger

from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.info_retriever import IInfoRetriever
from src.interfaces.nlp_processor import MLProcessor
from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter


class HtmlChopper(IContentAnalyzer):
    """
    Chops HTML content into parts and resolves it into an entity of type T.
    """

    summarizer: MLProcessor
    html_splitter: WikipediaAPIContentSplitter
    html_simplifier: MLProcessor
    html_retriever: IInfoRetriever
    html_pruner: MLProcessor[Section]

    def __init__(
        self,
        html_simplifier: MLProcessor,
        summarizer: MLProcessor,
        html_splitter: WikipediaAPIContentSplitter,
        html_retriever: IInfoRetriever,
        html_pruner: MLProcessor,
    ):
        self.html_splitter = html_splitter
        self.html_retriever = html_retriever
        self.summarizer = summarizer
        self.html_simplifier = html_simplifier
        self.html_pruner = html_pruner

    def process(
        self, content_id: str, html_content: str
    ) -> tuple[SourcedContentBase, list[Section]] | None:
        """

        Args:
            content_id (str): The unique identifier for the content being analyzed.
            html_content (str): The HTML content to analyze.

        Returns:
            List[BaseModel] | None: A list of `BaseModel` objects representing the extracted data,
            or None if the parsing fails or the content is not relevant.
        """

        if html_content is None or len(html_content) == 0:
            logger.warning(f"no HTML content found for content '{content_id}'")
            return None

        try:

            # retrieve permalink and title before content simplification
            permakink = self.html_retriever.retrieve_permalink(html_content)
            title = self.html_retriever.retrieve_title(html_content)

            # infobox sections titles are "Données clés"
            infobox = self.html_retriever.retrieve_infobox(
                html_content, format_as="list"
            )

            # simplify the HTML content
            simplified_content = self.html_simplifier.process(html_content)

            # split the HTML content into sections
            # preserving the hierarchy of sections
            sections = self.html_splitter.split(simplified_content)

            # add eventually orphaned sections
            # title of the section with orhans is set to "Introduction"
            orphaned_section = self.html_retriever.retrieve_orphans(
                simplified_content, position="start", sections_tag="section"
            )
            if orphaned_section is not None:
                sections.append(orphaned_section)
                logger.debug(
                    f"Added orphaned section to content '{content_id}': {orphaned_section.title}."
                )

            if infobox is not None:
                sections.append(infobox)
                logger.debug(f"Added infobox sections to content '{content_id}'.")

            if sections is None or len(sections) == 0:
                logger.warning(
                    f"no sections found, skipping the content '{content_id}'"
                )
                return None

            # base information
            base_info = SourcedContentBase(
                uid=content_id,
                title=title,
                permalink=permakink,
            )

            # convert to Text / Ascii
            sections = [self.html_pruner.process(section) for section in sections]

            for section in sections:
                if section is None:
                    continue

            # summarize the sections for better processing
            sections = [
                self.summarizer.process(section)
                for section in sections
                if section.content
            ]

            return base_info, sections

        except Exception as e:
            logger.error(
                f"Error while analyzing content '{content_id}': {e}",
            )

        return None
