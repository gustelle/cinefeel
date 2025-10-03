from loguru import logger

from src.entities.composable import Composable
from src.entities.content import Section
from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.content_splitter import IContentSplitter
from src.interfaces.nlp_processor import Processor


class Html2TextSectionsChopper(IContentAnalyzer):
    """
    Chops HTML content into sections, a section being identified by a given HTML tag (usually <section> or <h2>).
    It uses a `WikipediaAPIContentSplitter` to perform the splitting.
    """

    content_splitter: IContentSplitter
    post_processors: list[Processor]

    def __init__(
        self,
        content_splitter: IContentSplitter,
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
            tuple[Composable, list[Section]] | None: A tuple containing the base information of the `Composable`
                and the sections belonging to the content, or None if processing fails.
        """
        logger.info(f"Processing Html2TextSectionsChopper for content '{content_id}'")

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
