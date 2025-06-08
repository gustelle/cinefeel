import re

from bs4 import BeautifulSoup, Tag
from loguru import logger

from src.interfaces.content_splitter import IContentSplitter, Section


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

    def split(
        self,
        simplified_html: str,
        sections_tag_name: str = "section",
        root_tag: str = "body",
        flatten: bool = False,
    ) -> list[Section] | None:
        """
        Splits the HTML content into sections based on the specified tags.

        Args:
            html_content (str): The HTML content to be processed.
            sections_tag_name (str): The tag used to identify sections in the HTML content. Defaults to "section".
            root_tag (str): The root tag of the HTML content. Defaults to "body".
            flatten (bool): If True, flattens the hierarchy of sections.
                - Defaults to False in which case the hierarchy is preserved which means that sections have children sections.
                - When set to True, the sections are flattened, meaning that all sections are treated as top-level sections without any hierarchy.


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

            # but when flatten is set to True, the hierarchy is flattened:
            sections = splitter.split(html_content, flatten=True)
            # would return:
            [
                Section(
                    title="Main Section",
                    content="Content of the main section.",
                    children=[]
                ),
                Section(
                    title="Subsection",
                    content="Content of the subsection.",
                    children=[]
                )
            ]

            ```
        Raises:

        Returns:
            list[HtmlSection] | None: A list of HtmlSection objects containing the title and content of each section.
        """

        # cut simplified_html into sections
        simple_soup = BeautifulSoup(simplified_html, "html.parser")

        sections: list[Section] = []

        root = simple_soup.find(root_tag)

        if root is None:
            logger.warning(f"Root tag '{root_tag}' not found in the HTML content.")
            return None

        # find all sections with the specified tag, in recursive mode
        # thus if <section> is nested inside a <div> or any other tag,
        # it will still be found
        # if you'd not want this behavior, set recursive=False, but in this case
        # sections must be direct children of the root tag
        for section in root.find_all(sections_tag_name, recursive=flatten):

            # build the section from the tag
            built_section = self._build_section(
                tag=section,
                sections_tag_name=sections_tag_name,
                flatten=flatten,
            )

            # skip sections that are None
            if built_section is None:
                continue
            else:
                logger.debug(
                    f"> '{built_section.title}': {built_section.content[:50]}... ({len(built_section.children)} children)"
                )

            sections.append(built_section)

        return sections

    def _build_section(
        self,
        tag: Tag,
        sections_tag_name: str = "section",
        level: int = 1,
        flatten: bool = False,
    ) -> Section:
        """
        Builds a Section object from the given title and content.

        Args:
            tag (Tag): the current section tag being analyzed (and its content)
            sections_tag_name (str): The tag used to identify subsections. Defaults to "section".
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
            logger.debug(f"SKIPPED SECTION: '{section_title}'")
            return None

        if re.search(rf"{self.VOID_SECTION_MARKER}", tag.get_text(), re.IGNORECASE):
            logger.debug(f"VOID SECTION: '{section_title}'")
            return None

        # if the section contains children sections
        sub_sections = tag.find_all(sections_tag_name, recursive=flatten)

        if sub_sections:

            content = ""

            # find the content of the section
            # which does not belong to the children sections
            for node in tag.contents:

                # get the section content
                if isinstance(node, Tag) and node.name == sections_tag_name:
                    continue
                content += str(node).strip()

            # go deeper in the hierarchy
            children = [
                self._build_section(
                    child,
                    sections_tag_name=sections_tag_name,
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
            return None

        # make sure children are not None
        if children:
            children = [child for child in children if child is not None]

        return Section(title=section_title, content=content, children=children)
