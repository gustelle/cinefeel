from summarizer.sbert import SBertSummarizer

from src.interfaces.content_splitter import Section
from src.interfaces.nlp_processor import Processor
from src.settings import Settings


class SectionSummarizer(Processor[Section]):
    """
    summarize the content of a section.
    """

    settings: Settings
    summarizer: SBertSummarizer

    def __init__(self, settings: Settings):
        """
        Initialize the BERT similarity model.

        Args:
            model_name (str): The name of the BERT model to use.
        """
        self.settings = settings
        self.summarizer = SBertSummarizer(settings.bert_summary_model)

    def process(self, section: Section) -> Section | None:
        """
        Process a section to summarize its content if it exceeds the maximum length.

        The title of the section is preserved, and the content is summarized using a BERT model

        Children sections are processed as well recursively.

        Example:
        ```python
        section = Section(title="Example Section", content="This is a long content that needs summarization.")
        summarizer = SectionSummarizer(settings)
        summarized_section = summarizer.process(section)
        ```

        Args:
            section (Section): The section to process.

        Returns:
            Section: A new section with summarized content if the original content is too long,
                     otherwise the original section.
            None: If the section is None or empty.
        """
        return self._process_section(section)

    def _process_section(self, section: Section) -> Section:
        """
        Processes a single section to summarize its content.

        Args:
            section (Section): The section to process.

        Returns:
            Section: The processed section with summarized content.
        """
        new_content = section.content
        title = section.title

        if len(section.content) > self.settings.bert_summary_max_length:
            # logger.debug(f"section '{section.title}' is too long, summarizing it")
            new_content = self.summarizer.run(
                section.content, max_length=self.settings.bert_summary_max_length
            )

        children = None
        if section.children:
            children = []
            for child in section.children:
                children.append(
                    Section(
                        title=child.title,
                        content=child.content,
                        children=[
                            self._process_section(grandchild)
                            for grandchild in child.children
                        ],
                        media=child.media,
                    )
                )

        return Section(
            title=title, content=new_content, children=children, media=section.media
        )
