import html2text

from src.entities.content import Section
from src.interfaces.nlp_processor import Processor


class HTML2TextConverter(Processor[Section]):

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

        CHildren sections are processed as well recursively.

        Returns:
            Section: A new section with the HTML content and title converted to text.
        """

        return self._process_section(section)

    def _process_section(self, section: Section) -> Section:
        """
        Processes a single section to convert its HTML content and title to text.

        Args:
            section (Section): The section to process.

        Returns:
            Section: The processed section with HTML content and title converted to text.
        """

        content = self.html_to_text_transformer.handle(section.content)
        title = self.html_to_text_transformer.handle(section.title)

        if not content:
            return Section(title=title, content="", children=[], media=[])

        children = None
        if section.children:
            children = []
            for child in section.children:
                children.append(
                    Section(
                        title=self.html_to_text_transformer.handle(child.title),
                        content=self.html_to_text_transformer.handle(child.content),
                        children=[
                            self._process_section(child) for child in child.children
                        ],
                        media=child.media,
                    )
                )

        return Section(
            title=title, content=content, children=children, media=section.media
        )
