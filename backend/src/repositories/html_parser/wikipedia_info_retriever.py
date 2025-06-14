from io import StringIO
from typing import Generator, Literal

import pandas as pd
import polars as pl
from bs4 import BeautifulSoup, Tag
from loguru import logger
from pydantic import HttpUrl

from src.entities.content import PageLink, Section
from src.interfaces.info_retriever import IInfoRetriever, RetrievalError
from src.settings import WikiTOCPageConfig


class WikipediaInfoRetriever(IInfoRetriever):
    """
    This class is responsible for extracting Wikipedia data from a given HTML content.

    """

    _inner_page_id_prefix = "./"

    def retrieve_orphans(
        self,
        html_content: str,
        position: Literal["start", "beetwen", "end"] = "start",
        sections_tag: str = "section",
    ) -> Section:
        """
        Extracts orphan paragraphs from the HTML content based on the specified position.

        Only the "start" position is currently supported, which extracts paragraphs before the first section.

        Args:
            html_content (str): The HTML content to parse.
            position (str): The position of the orphan paragraph in the HTML content.
            sections_tag (str): The HTML tag that contains the sections. Defaults to "section".

        Returns:
            Section: A `Section` object containing the orphan paragraph.

        Raises:
            RetrievalError: if the orphan paragraph cannot be found in the HTML content.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        section_title = None

        orphans = []

        if position == "start":
            # extract the first paragraph
            section_title = "Introduction"
            for sibling in soup.find(sections_tag).previous_siblings:
                orphans.append(sibling.get_text(strip=True))
        else:
            raise RetrievalError(
                f"Position '{position}' is not yet supported for orphan paragraphs."
            )

        if not orphans:
            return None

        orphans.reverse()  # reverse the order to keep the original order

        logger.debug(
            f"Found {len(orphans)} orphan paragraphs at the {position} of the HTML content."
        )

        return Section(title=section_title, content="\n".join(orphans))

    def retrieve_permalink(self, html_content: str) -> HttpUrl:
        """
        Extracts the permalink from the given HTML content.

        Raises:
            WikiDataExtractionError: if the permalink cannot be found in the HTML content.
        """

        soup = BeautifulSoup(html_content, "html.parser")

        permalink_tag = soup.find("link", rel="canonical")
        if permalink_tag and permalink_tag.get("href"):
            return HttpUrl(permalink_tag.get("href"))
        else:
            # try another way
            permalink_tag = soup.find("link", attrs={"rel": "dc:isVersionOf"})
            if permalink_tag and permalink_tag.get("href"):
                value = permalink_tag.get("href")
                if not value.startswith("https://"):
                    # if the link is relative, we need to prepend the base URL
                    value = f"https://{value}"
                return HttpUrl(value)

        raise RetrievalError("Permalink not found in the HTML content.")

    def retrieve_title(self, html_content: str) -> str:
        """
        Extracts the title from the given HTML content.

        Args:
            html_content (str): The HTML content to parse.

        Returns:
            str: The extracted title from the HTML content.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        else:
            raise RetrievalError("Title not found in the HTML content.")

    def retrieve_inner_links(
        self, html_content: str, config: WikiTOCPageConfig
    ) -> list[PageLink]:
        """
        Parses the given HTML content and discovers wikipedia links to Wikipedia pages.
        A wikipedia link starts with `./` and is followed by the page ID.

        - When no `attrs` are provided, the function will look for all links in the HTML content,
        - If `attrs` are provided, it will look for links within the specified HTML structure.

        Example:
        - https://api.wikimedia.org/core/v1/wikipedia/fr/page/Liste_de_films_fran%C3%A7ais_sortis_en_1907/html

        Args:
            html_content (str): The HTML content to parse.
            config (WikiTOCPageConfig): The configuration for the page to be downloaded, which may include CSS selectors.

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
                config=WikiTOCPageConfig(
                    toc_css_selector=".wikitable td:nth-child(2)",
                    toc_content_type="person",

                )
            )
            # links = [
            #     PageLink(page_title="Lucien Nonguet", page_id="Lucien_Nonguet", content_type="person"),
            # ]
        ```

        Returns:
            list[PageLink]: a list of wikipedia pages, described by their IDs and eventually titles.

        Raises:
            WikiDataExtractionError: if the HTML content cannot be parsed or if the table structure is not as expected.
        """

        links: list[PageLink] = []
        soup = BeautifulSoup(html_content, "html.parser")

        # discover the structure of the HTML content
        # and extract the relevant links
        roots = (
            soup.select(config.toc_css_selector)
            if config.toc_css_selector
            else soup.find_all()
        )

        for root in roots:
            for link in self._parse_structure(root, config):
                links.append(link)

        return self._deduplicate_links(links)

    def _parse_structure(
        self,
        tag: Tag,
        config: WikiTOCPageConfig,
    ) -> Generator[PageLink, None, None]:

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
                    yield PageLink(
                        page_title=tag.get_text(strip=True),
                        page_id=linked_page_id,
                        content_type=config.toc_content_type,
                    )
                except Exception as e:
                    logger.error(f"Error creating WikiPageLink: {e} for tag: {tag}")
                    return

            case _:

                for child in tag.find_all(recursive=False):
                    # Recursively parse child elements
                    yield from self._parse_structure(child, config)

    def _deduplicate_links(self, links: list[PageLink]) -> list[PageLink]:
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

        return [PageLink(**row) for row in df.to_dicts()]

    def retrieve_infobox(
        self, html_content: str, format_as: Literal["table", "list"] = "list"
    ) -> Section | None:
        """
        Extracts the information table from the HTML content.

        Args:
            html_content (str): The HTML content to parse.
            format_as (Literal["table", "list"]): The format in which to return the infobox data.
                Defaults to "list". If "table", returns a the raw HTML table, otherwise returns an HTML list.

        Returns:
            list[Section] | None: A list of `Section` objects representing the infobox elements,
            or None if no infobox is found or if the table is empty.
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

        if format_as == "table":
            # return the raw HTML table
            content = content.find("table").prettify()

        else:
            # format the DataFrame as a list of values
            # split by a colon (:) and return as a Section object
            content = f"""
            <ul>
                {'\n'.join(f'<li>{row[0]}: {row[1]}</li>' for row in df.values)}
            </ul>
            """

        # convert the DataFrame to a list of Section objects
        info_table = Section(
            title="Données clés",
            content=content,
        )

        logger.debug(
            f"Info table found: {info_table.title} with content: {info_table.content}"
        )

        return info_table
