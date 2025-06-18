import html2text
from bs4 import BeautifulSoup

from src.entities.content import Section
from src.interfaces.nlp_processor import Processor


class TextSectionConverter(Processor[Section]):

    def _transform(self, content: str) -> str:
        """
        Initializes the HTML to text transformer with specific settings.
        """
        html_to_text_transformer = html2text.HTML2Text()
        html_to_text_transformer.ignore_links = False
        html_to_text_transformer.ignore_images = False
        html_to_text_transformer.ignore_tables = False
        html_to_text_transformer.ignore_emphasis = True
        html_to_text_transformer.body_width = 0  # Disable line wrapping

        content = self._add_space_between_tags(content)

        val = html_to_text_transformer.handle(content)

        return " ".join([c.strip() for c in val.split() if len(c.strip()) > 0])

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

        content = self._transform(section.content)
        title = self._transform(section.title)

        if not content:
            return Section(title=title, content="", children=[], media=[])

        children = None
        if section.children:
            children = []
            for child in section.children:

                # rework the title and content of the child section
                c_title = self._transform(child.title)
                c_content = self._transform(child.content)

                c_children = [self._process_section(child) for child in child.children]

                s = Section(
                    title=c_title,
                    content=c_content,
                    children=c_children,
                    media=child.media,
                )
                children.append(s)

        return Section(
            title=title,
            content=content,
            media=section.media,
            children=children,
        )

    def _add_space_between_tags(self, html: str) -> str:
        """
        Adds a space between HTML tags in the text.

        Args:
            text (str): The text to process.

        Returns:
            str: The processed text with spaces added between tags.
        """

        soup = BeautifulSoup(html, "html.parser")
        content = " ".join(str(node).strip() for node in soup.contents)

        # remove extra spaces
        # for example "<p>  </p>" becomes "<p></p>"
        return content
