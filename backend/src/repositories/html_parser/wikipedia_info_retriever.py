import re
from io import StringIO
from typing import Generator, Literal

import pandas as pd
import polars as pl
from bs4 import BeautifulSoup, Tag
from loguru import logger
from pydantic import HttpUrl, ValidationError

from src.entities.content import Media, PageLink, Section
from src.interfaces.info_retriever import IContentParser, RetrievalError
from src.settings import WikipediaTableOfContents

ORPHAN_SECTION_TITLE = "Introduction"
INFOBOX_SECTION_TITLE = "Données clés"


class WikipediaParser(IContentParser):
    """
    This class is responsible for extracting Wikipedia data from a given HTML content.

    """

    _inner_page_id_prefix = "./"

    # 70px-Nuvola_France_flag.svg.png
    _EXCLUDE_MEDIA_PATTERN = r".+flag(_.+)?\.svg.*|.+pencil\.svg.*|.+info.*\.svg.*"

    def retrieve_orphan_paragraphs(
        self,
        html_content: str,
    ) -> Section:
        """
        Extracts orphan paragraphs from the HTML content based on the specified position.
        Ophan paragraphs are paragraphs that are not attached to any section.

        Args:
            html_content (str): The HTML content to parse.

        Returns:
            Section: A `Section` object containing the orphan paragraph.

        Raises:
            RetrievalError: if the orphan paragraph cannot be found in the HTML content.
        """
        soup = BeautifulSoup(html_content, "html.parser")

        orphans = []
        media = []

        for node in soup.body.find_all(
            "p",
            # only direct children of the body tag
            recursive=False,
            # ignore empty paragraphs
            string=True,
        ):

            # don't strip the text, as it may contain important formatting
            orphans.append(node.get_text())

            media.extend(self.retrieve_media(str(node)))

        if not orphans:
            return None

        # media may be siblings of the paragraphs
        media.extend(
            self.retrieve_media(
                str(
                    soup.body.find_all(recursive=False),
                )
            )
        )

        orphans.reverse()  # reverse the order to keep the original order

        content = "\n".join(orphans)

        return Section(
            title=ORPHAN_SECTION_TITLE,
            content=content,
            media=media,
        )

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
        self, html_content: str, config: WikipediaTableOfContents
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
            soup.select(config.permalinks_selector)
            if config.permalinks_selector
            else soup.find_all()
        )

        for root in roots:
            for link in self._parse_structure(root, config):
                links.append(link)

        return self._deduplicate_links(links)

    def _parse_structure(
        self,
        tag: Tag,
        config: WikipediaTableOfContents,
    ) -> Generator[PageLink, None, None]:

        match tag.name:

            case "a":

                if not tag.get("href", "").startswith(self._inner_page_id_prefix):
                    return

                if "action=edit" in tag.get("href", ""):
                    return

                linked_page_id = tag.get("href").split("/")[-1]

                try:
                    yield PageLink(
                        page_title=tag.get_text(strip=True),
                        page_id=linked_page_id,
                        entity_type=config.entity_type,
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

        # get the media from the original HTML content
        media = self.retrieve_media(str(content))

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
            title=INFOBOX_SECTION_TITLE,
            content=content,
            media=media,
        )

        return info_table

    def retrieve_media(
        self, html_content: str, exclude_pattern: str = _EXCLUDE_MEDIA_PATTERN
    ) -> list[Media]:
        """
        Extracts media links from the HTML content.

        Args:
            html_content (str): The HTML content to parse.
            exclude_pattern (str, optional): A regex pattern to exclude certain media links.
                Defaults : excludes flags and certain icons.

        Args:
            html_content (str): The HTML content to parse.
        Returns:
            list[HttpUrl]: A list of media links (images, videos, etc.) found in the HTML content.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        media_ = []

        # Find all image tags
        for media_tag in soup.find_all(["video", "audio", "img"]):

            # case where the caption is in the sibling <figcaption> tag of the <img> tag
            caption = self._get_media_caption(media_tag)
            src = self._get_media_src(media_tag)

            if not src:
                continue
            elif exclude_pattern and re.search(exclude_pattern, src, re.IGNORECASE):
                continue

            try:
                media_type = (
                    "image"
                    if media_tag.name == "img"
                    else ("video" if media_tag.name == "video" else "audio")
                )
                media_.append(
                    Media(
                        uid=media_tag.get("id", src),
                        src=HttpUrl(src),
                        media_type=media_type,
                        caption=caption,
                    )
                )
            except ValidationError as e:
                logger.warning(f"Error creating Media object: {e} for tag: {media_tag}")

        return media_

    def _get_media_caption(self, tag: Tag) -> str:
        """
        Extracts the caption from a given HTML tag.

        Args:
            tag (Tag): The HTML tag to extract the caption from.

        Returns:
            str: The extracted caption text.
        """
        figcaption = tag.parent.find_next_sibling("figcaption")
        if figcaption:
            return figcaption.get_text(strip=True)
        return tag.get("alt", "")

    def _get_media_src(self, tag: Tag) -> str:
        """
        Extracts the media source URL from a given HTML tag.

        Args:
            tag (Tag): The HTML tag to extract the media source from.

        Returns:
            str: The extracted media source URL.
        """
        # case of images
        if tag.name == "img":
            src = tag.get("srcset", tag.get("src"))
            if isinstance(src, str):
                # srcset can be a string or a list of strings, we need to take the first one
                src = src.split(",")[0].strip().split(" ")[0]

            # ignore relative URLs
            if not src or re.match(r"^(\.\/|data:).+", src):
                return None

            # enventually, the src can be a relative URL, so we need to convert it to an absolute URL
            if src and src.startswith("//"):
                src = f"https:{src}"
            return src

        # case of videos and audios
        if tag.name in ["video", "audio"]:
            src = tag.get("src")
            if not src:
                # try to get the source from the source tag
                source_tag = tag.find("source")
                if source_tag:
                    src = source_tag.get("src")

            # ignore relative URLs
            if not src or re.match(r"^(\.\/|data:).+", src):
                return None

            if src and src.startswith("//"):
                src = f"https:{src}"
            return src

        # if the tag is not an image, video or audio, return an empty string
        return None
