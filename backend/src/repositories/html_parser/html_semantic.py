from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup
from htmlrag import clean_html
from pydantic import BaseModel


class HtmlSection(BaseModel):
    title: str
    content: str | None


class InfoBoxElement(BaseModel):
    title: str
    content: str | None


class HtmlSemantic:
    """
    Splits a given HTML content into sections based on the specified tags.
    """

    def split_sections(self, html_content: str) -> list[HtmlSection] | None:
        """
        Splits the HTML content into sections based on the specified tags.

        :param html_content: The HTML content to be split.
        :return: A list of sections.
        """

        # simplify the HTML content
        # for better embedding
        simplified_html = clean_html(html_content)

        # cut simplified_html into sections
        simple_soup = BeautifulSoup(simplified_html, "html.parser")
        doc_sections = simple_soup.find_all("section")

        sections: list[HtmlSection] = []

        for _, section in enumerate(doc_sections):
            # remove the section title
            section_title = section.find("h2")

            if section_title is None:
                # the section has no title
                # don't process it
                continue

            # take the raw text, not the html
            section_title_txt = section_title.get_text()
            section_content_el = section_title.find_next_sibling()

            VOID_SECTION = "cette section est vide"

            if (
                section_content_el is None
                or VOID_SECTION in section_content_el.get_text().lower()
            ):
                content = None
            else:
                content = section_content_el.get_text().strip()

            sections.append(
                HtmlSection(
                    title=section_title_txt,
                    content=content,
                )
            )

        return sections

    def parse_info_table(self, html_content: str) -> list[InfoBoxElement] | None:
        """
        Extracts the information table from the HTML content.

        :param html_content: The HTML content to be processed.
        :return: The information table as a string.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        content = soup.find("div", attrs={"class": "infobox"})

        if not content:
            return None

        # convert the HTML to text
        # using pandas
        df = pd.read_html(StringIO(content.find("table").prettify()))[0]
        if df.empty:
            return None

        # convert the DataFrame to a list of InfoBoxElement
        info_table = [
            InfoBoxElement(
                title=str(row[0]),
                content=str(row[1]) if len(row) > 1 else None,
            )
            for row in df.values
        ]

        return info_table
