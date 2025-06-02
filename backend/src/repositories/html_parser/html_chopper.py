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

    def analyze(
        self, content_id: str, html_content: str
    ) -> tuple[SourcedContentBase, list[Section]] | None:
        """
        Analyzes the HTML content and extracts relevant objects from it.

        TODO:
        - test non reg when no additional sections are found

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

            # simplify the HTML content
            simplified_content = self.html_simplifier.process(html_content)

            # split the HTML content into sections
            # TODO: here, we could take advantage of the sections hierarchy
            # and split the content into sections based on the hierarchy
            sections = self.html_splitter.split(simplified_content)

            # add eventually orphaned sections
            orphaned_section = self.html_retriever.retrieve_orphans(
                simplified_content, position="start", sections_tag="section"
            )
            if orphaned_section is not None:
                sections.append(orphaned_section)

            if sections is None or len(sections) == 0:
                logger.warning(
                    f"no sections found, skipping the content '{content_id}'"
                )
                return None

            additional_sections = self.html_retriever.retrieve_infoboxes(
                simplified_content
            )

            if additional_sections is not None and len(additional_sections) > 0:
                sections.extend(additional_sections)

            # base information
            base_info = SourcedContentBase(
                uid=content_id,
                title=title,
                permalink=permakink,
            )

            # convert to Text / Ascii
            sections = [self.html_pruner.process(section) for section in sections]

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
