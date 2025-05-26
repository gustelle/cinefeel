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
        Find the most similar `Section` to the given title within the list of sections.

        Args:
            title (str): The title to find the most similar section for.
            sections (list[Section]): The list of sections to search within.

        Returns:
            str | None: The most similar section title, or None if no similar title is found.
        """
        new_content = self.summarizer.run(section.content)

        return Section(title=section.title, content=new_content)
