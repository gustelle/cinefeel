from loguru import logger

from src.entities.content import Section
from src.entities.source import BaseInfo
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.info_retriever import IInfoRetriever
from src.interfaces.similarity import MLProcessor
from src.repositories.html_parser.html_splitter import HtmlSplitter


class HtmlChopper(IContentAnalyzer):
    """
    Chops HTML content into parts and resolves it into an entity of type T.
    """

    summarizer: MLProcessor
    html_splitter: HtmlSplitter
    html_simplifier: MLProcessor
    html_retriever: IInfoRetriever

    def __init__(
        self,
        html_simplifier: MLProcessor,
        summarizer: MLProcessor,
        html_splitter: HtmlSplitter,
        html_retriever: IInfoRetriever,
    ):
        self.html_splitter = html_splitter
        self.html_retriever = html_retriever
        self.summarizer = summarizer
        self.html_simplifier = html_simplifier

    def analyze(
        self, content_id: str, html_content: str
    ) -> tuple[BaseInfo, list[Section]] | None:
        """
        Analyzes the HTML content and extracts relevant objects from it.

        TODO:
        - test BaseInfo is always present in the sections returned
        - test error catched when permalink or title is not found

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

        # retrieve permalink and title before content simplification
        permakink = self.html_retriever.retrieve_permalink(html_content)
        title = self.html_retriever.retrieve_title(html_content)

        if title is None or permakink is None:
            logger.warning(
                f"Cannot process '{content_id}', title or permalink not found."
            )
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

        additional_sections = self.html_retriever.retrieve_infoboxes(html_content)

        if additional_sections is not None and len(additional_sections) > 0:
            sections.extend(additional_sections)

        try:

            # base information
            base_info = BaseInfo(
                title=title,
                permalink=permakink,
            )

            return base_info, sections

        except Exception as e:
            logger.error(
                f"Error while analyzing content '{content_id}': {e}",
                exc_info=True,
            )

        return None
