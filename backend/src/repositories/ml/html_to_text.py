
import html2text

from src.entities.content import Section
from src.interfaces.nlp_processor import MLProcessor


class HTML2TextConverter(MLProcessor[Section]):

    html_to_text_transformer: html2text.HTML2Text

    def __init__(self):
        self.html_to_text_transformer = html2text.HTML2Text()
        self.html_to_text_transformer.ignore_links = False
        self.html_to_text_transformer.ignore_images = False
        self.html_to_text_transformer.ignore_tables = False
        self.html_to_text_transformer.ignore_emphasis = True

    def process(self, section: Section) -> Section:
        """
        proceeds to a text conversion of the HTML content of a section, as well as the title.

        Returns:
            Section: A new section with the HTML content and title converted to text.
        """

        content = self.html_to_text_transformer.handle(section.content)
        title = self.html_to_text_transformer.handle(section.title)

        if not content:
            return Section(title=title, content="")

        return Section(title=title, content=content)
