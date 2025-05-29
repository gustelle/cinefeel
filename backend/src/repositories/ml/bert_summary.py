from loguru import logger
from summarizer.sbert import SBertSummarizer

from src.interfaces.content_splitter import Section
from src.interfaces.similarity import MLProcessor
from src.settings import Settings


class SectionSummarizer(MLProcessor[Section]):
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
        """_summary_

        Args:
            section (Section): _description_

        Returns:
            Section | None: _description_
        """
        new_content = section.content

        if len(section.content) > self.settings.bert_summary_max_length:
            logger.debug(f"section '{section.title}' is too long, summarizing it")
            new_content = self.summarizer.run(
                section.content, max_length=self.settings.bert_summary_max_length
            )
        else:  # section is short enough, no need to summarize
            logger.debug(
                f"section '{section.title}' is short enough ({len(section.content)} characters)"
            )

        return Section(title=section.title, content=new_content)
