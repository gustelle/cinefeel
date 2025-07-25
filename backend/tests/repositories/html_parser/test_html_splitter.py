from pathlib import Path

import pytest

from src.entities.composable import Composable
from src.repositories.html_parser.html_splitter import (
    Section,
    WikipediaAPIContentSplitter,
)
from src.repositories.html_parser.wikipedia_info_retriever import (
    ORPHAN_SECTION_TITLE,
    WikipediaParser,
)
from src.settings import Settings

from .stubs.stub_pruner import DoNothingPruner

current_dir = Path(__file__).parent


def test_split_subsections():

    # given
    html_file = current_dir / "test_html/nested_sections.html"
    html_content = html_file.read_text(encoding="utf-8")
    pruner = DoNothingPruner()
    settings = Settings(
        sections_min_length=1,  # Set to 1 to ensure all sections are processed
    )

    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=pruner, settings=settings
    )
    # when
    base_info, sections = semantic.split("1", html_content)
    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert sections is not None
    assert sections[0].title == "Biographie"
    assert sections[0].children[0].title == "1770-1792: jeunesse à Bonn"
    assert sections[0].children[0].children[0].title == "Origines et enfance"


def test_split_complex_page(read_beethoven_html):
    """
    Test the split_sections method of the HtmlSemantic class.
    """
    # given
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    base_info, sections = semantic.split("1", read_beethoven_html)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert sections is not None
    assert len(sections) > 0
    assert all(
        isinstance(section, Section) for section in sections
    ), "All sections should be of type HtmlSection"


def test_split_melies_page(read_melies_html):
    """
    Test the split_sections method of the HtmlSemantic class.
    """
    # given
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(),
        pruner=DoNothingPruner(),
        settings=Settings(
            sections_min_length=1  # Set to 1 to ensure all sections are processed
        ),
    )

    # when
    # we must flatten here because the root element has no direct section child
    base_info, sections = semantic.split("1", read_melies_html)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert sections is not None
    assert len(sections) > 0

    # test a children section
    assert any("Biographie" == section.title for section in sections)
    for section in sections:
        if section.title == "Biographie":
            assert len(section.children) > 0, "Should contain children sections"
            assert any(
                "Jeunesse" == child.title for child in section.children
            ), "Should contain 'Jeunesse' section in children"
            break


def test_split_with_root_tag(read_beethoven_html):

    # given
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(),
        pruner=DoNothingPruner(),
        settings=Settings(
            sections_min_length=1  # Set to 1 to ensure all sections are processed
        ),
    )

    # when
    # we must flatten here because the root element has no direct section child
    base_info, sections = semantic.split("1", read_beethoven_html, root_tag_name="body")

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert sections is not None
    assert len(sections) > 0
    assert any(
        section.title == "Biographie" and len(section.children) > 0
        for section in sections
    ), "Should contain 'Biographie' section with children"


def test_split_ignores_non_significant_sections(read_beethoven_html):

    # given
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    base_info, sections = semantic.split("1", read_beethoven_html)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert sections is not None
    assert all(
        "notes et références" not in section.title.lower() for section in sections
    )
    assert all("voir aussi" not in section.title.lower() for section in sections)


def test_split_sections_no_title():

    # given
    # an valid html file with a section that has no title
    html_file = current_dir / "test_html/no_section_title.html"
    html_content = html_file.read_text(encoding="utf-8")
    info_retriever = WikipediaParser()

    semantic = WikipediaAPIContentSplitter(
        parser=info_retriever, pruner=DoNothingPruner()
    )

    # when
    base_info, sections = semantic.split("1", html_content)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert len(sections) > 0
    assert sections[0].title == ORPHAN_SECTION_TITLE


def test_split_sections_void_section():

    # given
    html_file = current_dir / "test_html/void_section.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    base_info, sections = semantic.split("1", html_content, section_tag_name="div")

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)

    assert len(sections) == 0


def test_split_title_is_not_pure_text():
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test HTML without title</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <section>
        <h2><b>Section Title</b></h2>
        <p>This is the content of the section.</p>
    </section>
    </body>
    </html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    base_info, sections = semantic.split("1", html_content)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert len(sections) == 1


def test_split_title_is_removed_from_content():
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test HTML without title</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <section>
        <h2>Section Title</h2>
        <p>This is the content of the section.</p>
    </section>
    </body>
    <html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    base_info, sections = semantic.split("1", html_content)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert len(sections) == 1


def test_split_sections_no_title_and_no_content():
    "A section with no title and no content should still be created as 'orphan'"

    # given
    html_content = """
    <html>
        <head>
            <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
            <title>Test HTML section without title and content</title>
        </head>
        <body>
            <section>
                <p id="mwBQ"></p>
            </section>
        </body>
    </html>
    """
    retriever = WikipediaParser()
    semantic = WikipediaAPIContentSplitter(parser=retriever, pruner=DoNothingPruner())

    # when
    base_info, sections = semantic.split("1", html_content)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert len(sections) == 0


def test_split_preserve_hierarchy():
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test HTML without title</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <section>
        <h2>Section 1</h2>
        <p>Content of section 1</p>
        <section>
            <h3>Nested Section 1.1</h3>
            <p>Content of nested section 1.1</p>
        </section>
        <section>
            <h3>Nested Section 1.2</h3>
            <p>Content of nested section 1.2</p>
        </section>
    </section>
    </body>
    </html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(),
        pruner=DoNothingPruner(),
        settings=Settings(sections_min_length=1),
    )
    # when
    base_info, sections = semantic.split("1", html_content)

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert len(sections) == 1
    assert sections[0].title == "Section 1"
    assert len(sections[0].children) == 2
    assert sections[0].children[0].title == "Nested Section 1.1"
    assert sections[0].children[1].title == "Nested Section 1.2"


def test_split_nested_sections_with_div():
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test nested div sections</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <div id="...">
        <h2>Section 1</h2>
        <p>Content of section 1</p>
        <div>
            <h3>Nested Section 1.1</h3>
            <p>Content of nested section 1.1</p>
        </div>
        <div>
            <h3>Nested Section 1.2</h3>
            <p>Content of nested section 1.2</p>
        </div>
    </div>
    </body>
    </html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(),
        pruner=DoNothingPruner(),
        settings=Settings(sections_min_length=1),
    )

    # when
    base_info, sections = semantic.split(
        "1",
        html_content,
        section_tag_name="div",
    )

    # then
    assert base_info is not None
    assert isinstance(base_info, Composable)
    assert len(sections) == 1
    assert sections[0].title == "Section 1"
    assert len(sections[0].children) == 2
    assert sections[0].children[0].title == "Nested Section 1.1"
    assert sections[0].children[1].title == "Nested Section 1.2"


def test_pruner_is_called():
    # given
    html_file = current_dir / "test_html/nested_sections.html"
    html_content = html_file.read_text(encoding="utf-8")
    pruner = DoNothingPruner()

    semantic = WikipediaAPIContentSplitter(parser=WikipediaParser(), pruner=pruner)

    # when
    semantic.split("1", html_content)

    # then
    assert pruner.is_called, "Pruner should be called during the split process"


def test_sections_are_enriched_with_media():
    # given
    # a valid HTML file with sections that should be enriched with media
    html_file = current_dir / "test_html/sections_with_media.html"
    html_content = html_file.read_text(encoding="utf-8")
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(),
        pruner=DoNothingPruner(),
        settings=Settings(
            sections_min_length=1  # Set to 1 to ensure all sections are processed
        ),
    )

    # when
    _, sections = semantic.split("1", html_content)
    # then
    assert all(
        len(section.media) > 0 for section in sections
    ), "All sections should bhave media"
    assert len(sections[0].children[0].media) > 0
    assert (
        len(sections[0].children[0].children[0].media) > 0
    ), "Grand Children sections should have media"


@pytest.mark.todo
def test_missing_tests():
    """
    This is a placeholder for tests that are not yet implemented.
    The following tests should be implemented:

    - test orphans sections are retrieved correctly
    - test that infobox is retrieved correctly
    - test base information is retrieved correctly
    - test extract section titles
    """
    pass


def test_empty_sections_are_filtered():
    """
    Test that empty sections are filtered out.
    """
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test HTML with empty sections</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <section>
        <h2>Empty Section</h2>
        <p></p>
    </section>
    </body>
    </html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    _, sections = semantic.split("1", html_content)

    # then
    assert len(sections) == 0, "No sections should be returned for empty sections"


def test_small_sections_are_merged():
    """
    Test that small sections are merged correctly,
    for instance small sections are merged into their parent section

    """
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test HTML with small sections</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <section>
        <h2>Small Section</h2>
        <p>This is a small section with some content.</p>
    </section>
    <section>
        <h2>Small Section 2</h2>
        <p>This is a small section with some content.</p>
    </section>
    </body>
    </html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    _, sections = semantic.split("1", html_content)

    # then
    assert len(sections) == 1, "Only one section should be returned for small sections"
    assert (
        sections[0].title == "Small Section - Small Section 2"
    ), "Section titles should be merged"


def test_small_children_sections_are_merged_into_their_parent():
    """
    Test that small sections are merged correctly,
    for instance children sections are merged into their parent section
    """
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test HTML with medium sections</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <section>
        <h2>Small Section</h2>
        <p>This is a small section with some content.</p>
        <section>
            <h3>Subsection</h3>
            <p>This is a subsection with some content.</p>
        </section>
    </section>
    </body>
    </html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    _, sections = semantic.split("1", html_content)

    # then

    assert len(sections) > 0, "Sections should be returned for medium sections"
    assert len(sections[0].children) == 0, "No children sections should remain"
    assert (
        "<p>This is a subsection with some content.</p>" in sections[0].content
    ), "Content of subsection should be merged into parent section"


def test_flags_and_icons_are_excluded_from_media():
    """
    Test that flags and icons are excluded from media.
    """
    # given
    html_content = """
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test HTML with flags and icons</title>
        <link rel="dc:isVersionOf" href="//fr.wikipedia.org/wiki/test"/>
    </head>
    <body>
    <section>
        <h2>Section with Flag</h2>
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Nuvola_France_flag.svg/70px-Nuvola_France_flag.svg.png" alt="Flag" />
        <p>Content of section with flag.</p>
    </section>
    </body>
    </html>
    """
    semantic = WikipediaAPIContentSplitter(
        parser=WikipediaParser(), pruner=DoNothingPruner()
    )

    # when
    _, sections = semantic.split("1", html_content)

    # then
    assert len(sections) == 1, "One section should be returned"
    assert len(sections[0].media) == 0
