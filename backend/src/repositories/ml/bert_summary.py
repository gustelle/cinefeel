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
        """

        TODO:
        - add param `max_length` to limit the length of the summary.
        """
        new_content = self.summarizer.run(section.content)

        return Section(title=section.title, content=new_content)
