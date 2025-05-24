from io import StringIO
from typing import Generator

import pandas as pd
import polars as pl
from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.entities.content import InfoBoxElement, WikiPageLink
from src.interfaces.extractor import IHtmlExtractor


class WikiDataExtractionError(Exception):
    pass


class WikipediaExtractor(IHtmlExtractor):
    """
    This class is responsible for extracting Wikipedia links from a given HTML content.

    """

    _inner_page_id_prefix = "./"

    def retrieve_inner_links(
        self,
        html_content: str,
        css_selector: str | None = None,
    ) -> list[WikiPageLink]:
        """
        Parses the given HTML content and discovers wikipedia links to Wikipedia pages.
        A wikipedia link starts with `./` and is followed by the page ID.

        - When no `attrs` are provided, the function will look for all links in the HTML content,
        - If `attrs` are provided, it will look for links within the specified HTML structure.

        Example:
        - https://api.wikimedia.org/core/v1/wikipedia/fr/page/Liste_de_films_fran%C3%A7ais_sortis_en_1907/html

        Args:
            html_content (str): The HTML content to parse.
            css_selector (str): filter the links within the targeted html structure. Defaults to None.
                Example: "td:nth-child(2)" to filter links belonging to the second column of a table.

        Example:
        ```
            html_content =
            <table class="wikitable">
                <tr>
                    <th>Titre</th>
                    <th>Réalisateur</th>
                </tr>
                <tr>
                    <td><a href="./Film_Title">Film Title</a></td>
                    <td><a rel="mw:WikiLink" href="./Lucien_Nonguet" title="Lucien Nonguet" id="mwFw">Lucien Nonguet</a></td>
                </tr>
            </table>

            links = extractor.retrieve_inner_links(
                html_content,
                css_selector="table td:nth-child(2)"
            )
            # links = [
            #     WikiPageLink(page_title="Lucien Nonguet", page_id="Lucien_Nonguet"),
            # ]
        ```

        Returns:
            list[WikiPageLink]: a list of wikipedia pages, described by their IDs and eventually titles.

        Raises:
            WikiDataExtractionError: if the HTML content cannot be parsed or if the table structure is not as expected.
        """

        links: list[WikiPageLink] = []
        soup = BeautifulSoup(html_content, "html.parser")

        # discover the structure of the HTML content
        # and extract the relevant links
        roots = soup.select(css_selector) if css_selector else soup.find_all()

        for root in roots:
            for link in self._parse_structure(root):
                links.append(link)

        return self._deduplicate_links(links)

    def _parse_structure(
        self,
        tag: Tag,
    ) -> Generator[WikiPageLink, None, None]:

        match tag.name:

            case "a":

                if not tag.get("href", "").startswith(self._inner_page_id_prefix):
                    logger.debug(f"Skipping external link: {tag.get('href')}")
                    return

                if "action=edit" in tag.get("href", ""):
                    # the page does not exist
                    logger.debug(
                        f"Skipping link to non existing page: {tag.get('href')}"
                    )
                    return

                linked_page_id = tag.get("href").split("/")[-1]

                try:
                    yield WikiPageLink(
                        page_title=tag.get_text(strip=True),
                        page_id=linked_page_id,
                    )
                except Exception as e:
                    logger.error(f"Error creating WikiPageLink: {e} for tag: {tag}")
                    return

            case _:

                for child in tag.find_all(recursive=False):
                    # Recursively parse child elements
                    yield from self._parse_structure(child)

    def _deduplicate_links(self, links: list[WikiPageLink]) -> list[WikiPageLink]:
        """
        Deduplicates the list of links based on their page_id.

        Args:
            links (list[WikiPageLink]): The list of links to deduplicate.

        Returns:
            list[WikiPageLink]: The deduplicated list of links.
        """
        if not links or len(links) == 0:
            return []

        df = pl.from_records(links)
        df = df.unique(subset=["page_id"])

        return [WikiPageLink(**row) for row in df.to_dicts()]

    def retrieve_infoboxes(self, html_content: str) -> list[InfoBoxElement] | None:
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
