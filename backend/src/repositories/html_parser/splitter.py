import re

from bs4 import BeautifulSoup
from htmlrag import clean_html

from src.interfaces.content_splitter import IContentSplitter, Section


class HtmlSplitter(IContentSplitter):
    """
    Splits a given HTML content into sections based on the specified tags.
    """

    VOID_SECTION_MARKER = "cette section est vide"

    SKIPPED_SECTIONS = [
        "notes et références",
        "voir aussi",
        "liens externes",
        "publications",
    ]

    def split(
        self,
        html_content: str,
    ) -> list[Section] | None:
        """
        Splits the HTML content into sections based on the specified tags.

        the sections rendered are simplified using `htmlrag` to remove unnecessary scripts and styles
        and to make the text easier for embedding.

        Example:
        ```html
        <h2>Section 1</h2>
        <p>Content of section 1</p>
        <p>Content of section 1 continued</p>
        <h2>Section 2</h2>
        <p>Content of section 2</p>
        <div>Content of section 2 continued</div>
        ```


        Args:
            html_content (str): The HTML content to be processed.

        Returns:
            list[HtmlSection] | None: A list of HtmlSection objects containing the title and content of each section.
        """

        _SKIPPED_TAGS = [
            "figcaption",
        ]

        # simplify the HTML content
        # for better embedding
        simplified_html = clean_html(html_content)

        # cut simplified_html into sections
        simple_soup = BeautifulSoup(simplified_html, "html.parser")

        sections: list[Section] = []

        for section_title in simple_soup.find_all("h2"):

            if section_title is None or len(section_title.get_text().strip()) == 0:
                # logger.debug(f"Skipping void section: {section_title.get_text()}")
                continue

            # if it's a note section
            if section_title.get_text().strip().casefold() in self.SKIPPED_SECTIONS:
                # logger.debug(f"Skipping note section: {section_title.get_text()}")
                continue

            # take all <div> and <p> tags next to the title
            # and before the next title
            after_section_ = section_title.find_all_next()
            section_contents: list[str] = []

            for content in after_section_:

                if content.name == "h2":
                    # we reached the next section
                    # break the loop
                    break

                text = content.get_text().strip()

                # if the text is empty or void
                # or if the content belongs to a skipped tag
                if (
                    re.match(self.VOID_SECTION_MARKER, text, re.IGNORECASE)
                    or content.name in _SKIPPED_TAGS
                    or len(text) == 0
                ):
                    continue

                # for li tags
                # we need to join the text with a space
                # sometimes the current node is a <a> tag belonging to a <li> tag
                _list_markers = ["ul", "ol", "li"]

                if (
                    content.name in _list_markers
                    or content.parent.name in _list_markers
                ):
                    text = f"- {text}\n"

                # make sure the text ends with a dot and space
                # this will improve the embedding
                # and the readability of the text
                elif not text.endswith("."):
                    text += ". "

                section_contents.append(text)

            if len(section_contents) == 0:
                # logger.debug(f"Skipping void section: {section_title.get_text()}")
                continue

            section_contents.append("\n")
            sections.append(
                Section(
                    title=section_title.get_text().strip(),
                    content=" ".join(section_contents).strip(),
                )
            )

        return sections
