from loguru import logger

from src.entities.composable import Composable
from src.entities.content import Section
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.nlp_processor import Processor
from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter


class Html2TextSectionsChopper(IContentAnalyzer):
    """
    Chops HTML content into textual parts

    """

    content_splitter: WikipediaAPIContentSplitter
    post_processors: list[Processor]

    def __init__(
        self,
        content_splitter: WikipediaAPIContentSplitter,
        post_processors: list[Processor] = None,
    ):
        self.content_splitter = content_splitter
        self.post_processors = post_processors

    def process(
        self, content_id: str, html_content: str
    ) -> tuple[Composable, list[Section]] | None:
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

            # split the HTML content into sections
            base_info, sections = self.content_splitter.split(content_id, html_content)

            if sections is None or len(sections) == 0:
                logger.warning(
                    f"no sections found, skipping the content '{content_id}'"
                )
                return None

            # post processing of sections
            if self.post_processors:
                for processor in self.post_processors:
                    sections = [processor.process(section) for section in sections]

            return base_info, sections

        except Exception:
            import traceback

            logger.error(
                f"Error while processing content '{content_id}': {traceback.format_exc()}"
            )

        return None
