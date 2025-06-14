import re

from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.entities.source import SourcedContentBase
from src.interfaces.content_splitter import IContentSplitter, Section
from src.interfaces.info_retriever import IInfoRetriever
from src.interfaces.nlp_processor import Processor


class WikipediaAPIContentSplitter(IContentSplitter):
    """
    Splits a given HTML content into sections based on the specified tags.

    **This class is really tailored for the contents coming from the Wikipedia API**, which are different from the ones
    coming from the HTML pages. Indeed, API contents are clustered into sections

    See examples here: https://api.wikimedia.org/core/v1/wikipedia/fr/page/Ludwig_van_Beethoven/html


    """

    VOID_SECTION_MARKER = "cette section est vide"

    SKIPPED_SECTIONS = [
        "notes et références",
        "voir aussi",
        "liens externes",
        "publications",
    ]

    def __init__(
        self, info_retriever: IInfoRetriever, html_simplifier: Processor = None
    ):
        """
        Initializes the WikipediaAPIContentSplitter.
        """
        self.info_retriever = info_retriever
        self.html_simplifier = html_simplifier

    def split(
        self,
        uid: str,
        html_content: str,
        section_tag_name: str = "section",
        root_tag_name: str = "body",
    ) -> tuple[SourcedContentBase, list[Section]] | None:
        """
        Splits the HTML content into sections based on the specified tags.

        TODO:
        - test that sections are enriched with media
        - test orphans sections are retrieved correctly
        - test that infobox is retrieved correctly
        - test base information is retrieved correctly
        - test extract section titles

        Args:
            uid (str): The unique identifier for the content.
            html_content (str): The HTML content to be processed.
            section_tag_name (str): The tag used to identify sections in the HTML content. Defaults to "section"
            root_tag_name (str): The tag used to identify the root of the HTML content. Defaults to "body".

        Example:
            ```python
            # example with nested sections:
            html_content = "<section><h2>Main Section</h2><p>Content of the main section.</p><section><h3>Subsection</h3><p>Content of the subsection.</p></section></section>"
            splitter = WikipediaAPIContentSplitter()
            sections = splitter.split(html_content, flatten=False)
            # would return:
            [
                Section(
                    title="Main Section",
                    content="Content of the main section.",
                    children=[
                        Section(
                            title="Subsection",
                            content="Content of the subsection.",
                            children=[]
                        )
                    ]
                )
            ]

            ```

        Returns:
            tuple[SourcedContentBase, list[Section]] | None: A tuple containing the base content and a list of sections.
        """

        # retrieve permalink and title before content simplification
        permakink = self.info_retriever.retrieve_permalink(html_content)
        title = self.info_retriever.retrieve_title(html_content)

        base_content = SourcedContentBase(
            uid=uid,
            title=title,
            permalink=permakink,
        )

        sections: list[Section] = []

        # add eventually orphaned sections
        # title of the section with orhans is set to "Introduction"
        orphaned_section = self.info_retriever.retrieve_orphan_paragraphs(
            html_content,
        )

        if orphaned_section is not None:
            sections.append(orphaned_section)

        # infobox
        infobox = self.info_retriever.retrieve_infobox(html_content)
        if infobox is not None:
            sections.append(infobox)

        if self.html_simplifier is not None:
            html_content = self.html_simplifier.process(html_content)

        # cut simplified_html into sections
        simple_soup = BeautifulSoup(html_content, "html.parser")

        # search starting from the root tag
        # if no root tag is found, search from the <html> tag
        # NB: here we must search recursively
        # because the HTML content is not guaranteed to have a <body> tag
        root = simple_soup.find(
            root_tag_name,
        ) or simple_soup.find("html")

        if root is not None:

            for tag in root.find_all(
                section_tag_name,
                recursive=False,
            ):

                # build the section from the tag
                built_section = self._build_section(
                    tag=tag,
                    section_tag_name=section_tag_name,
                )

                # skip sections that are None
                if built_section is None:
                    continue

                sections.append(built_section)

        return base_content, sections

    def _build_section(
        self,
        tag: Tag,
        section_tag_name: str = "section",
        level: int = 1,
    ) -> Section:
        """
        Builds a Section object from the given title and content.

        Args:
            tag (Tag): the current section tag being analyzed (and its content)
            section_tag_name (str): The tag used to identify subsections. Defaults to "section".
            level (str): The level of the section, Defaults to "1".
                levels are defined as follows:
                - 1: correspond to <h2> titles
                - 2: correspond to <h3> titles
                - ... and so on.

        Returns:
            Section: A Section object containing the title and content.
        """

        title_tag_name = f"h{level + 1}"
        children = []

        section_title = ""
        title_tag = tag.find(title_tag_name)

        # if it's a subsection
        if title_tag is not None:
            # if it's a main section
            # take the title from the first <h2> tag
            # NB: it's not the job of this class to prune the HTML content
            # so we take the title as it is, e.g. with nested html tags <h2><b>Section Title</b></h2>
            section_title = "".join(str(node).strip() for node in title_tag.contents)

        if section_title is not None and any(
            ignored_title in section_title.casefold()
            for ignored_title in self.SKIPPED_SECTIONS
        ):
            logger.debug(
                f"Skipping section with title '{section_title}' as it is in the ignored sections list."
            )
            return None

        if re.search(rf"{self.VOID_SECTION_MARKER}", tag.get_text(), re.IGNORECASE):
            logger.debug(
                f"Skipping section with title '{section_title}' as it is marked as empty."
            )
            return None

        # if the section contains children sections
        sub_sections = tag.find_all(section_tag_name, recursive=False)

        if sub_sections:

            content = ""

            # find the content of the section
            # which does not belong to the children sections
            for node in tag.contents:

                # get the section content
                if isinstance(node, Tag) and node.name == section_tag_name:
                    continue
                content += str(node).strip()

            # go deeper in the hierarchy
            children = [
                self._build_section(
                    child,
                    section_tag_name=section_tag_name,
                    level=level + 1,
                )
                for child in sub_sections
            ]

        else:

            # no children sections
            content = str(tag).strip()

            # take the content of the section
            content = "".join(str(node).strip() for node in tag.contents)

            # remove title tag from content
            content = re.sub(
                rf"<{title_tag_name}.*?>.+</{title_tag_name}>",
                "",
                content,
                flags=re.DOTALL | re.IGNORECASE,
            )

        # check the text content of the section is not empty
        # to avoid empty sections like <section><p id="mwBQ"></p></section>
        if content is None or not content.strip() or not tag.get_text(strip=True):
            logger.debug(
                f"Skipping section with title '{section_title}' as it has no content."
            )
            return None

        # make sure children are not None
        if children:
            children = [child for child in children if child is not None]

        return Section(
            title=section_title,
            content=content,
            children=children,
            media=self.info_retriever.retrieve_media(html_content=content),
        )
