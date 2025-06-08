from pathlib import Path

from src.repositories.html_parser.html_splitter import (
    Section,
    WikipediaAPIContentSplitter,
)

current_dir = Path(__file__).parent


def test_split_complex_page(read_beethoven_html):
    """
    Test the split_sections method of the HtmlSemantic class.
    """
    # given
    semantic = WikipediaAPIContentSplitter()

    # when
    # we must flatten here because the root element has no direct section child
    sections = semantic.split(read_beethoven_html, flatten=True)

    # then
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
    semantic = WikipediaAPIContentSplitter()

    # when
    # we must flatten here because the root element has no direct section child
    sections = semantic.split(read_melies_html, flatten=True)

    # then
    assert sections is not None
    assert len(sections) > 0

    for section in sections:
        print(f"Section title: {section.title}")

    # test a children section
    assert any(
        '<h3 id="Jeunesse">' in section.content for section in sections
    ), "Should contain 'Jeunesse' section with children"


def test_split_with_root_tag(read_beethoven_html):

    # given
    semantic = WikipediaAPIContentSplitter()

    # when
    # we must flatten here because the root element has no direct section child
    sections = semantic.split(read_beethoven_html, flatten=False, root_tag="body")

    # then
    assert sections is not None
    assert len(sections) > 0
    assert any(
        section.title == "Biographie" and len(section.children) > 0
        for section in sections
    ), "Should contain 'Biographie' section with children"


def test_split_ignores_non_significant_sections(read_beethoven_html):

    # given
    semantic = WikipediaAPIContentSplitter()

    # when
    sections = semantic.split(read_beethoven_html, flatten=True)

    # then
    assert all(
        "notes et références" not in section.title.lower() for section in sections
    )
    assert all("voir aussi" not in section.title.lower() for section in sections)


def test_split_sections_no_title():
    # given
    html_file = current_dir / "test_html/no_title.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = WikipediaAPIContentSplitter()

    # when
    sections = semantic.split(html_content, sections_tag_name="div")

    # then
    assert len(sections) == 1
    assert sections[0].title == ""


def test_split_sections_void_section():

    # given
    html_file = current_dir / "test_html/void_section.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = WikipediaAPIContentSplitter()

    # when
    sections = semantic.split(html_content, sections_tag_name="div")

    # then
    assert len(sections) == 0


def test_split_title_is_not_pure_text():
    # given
    html_content = """
    <body>
    <section>
        <h2><b>Section Title</b></h2>
        <p>This is the content of the section.</p>
    </section>
    </body>
    """
    semantic = WikipediaAPIContentSplitter()
    # when
    sections = semantic.split(html_content)
    # then
    assert len(sections) == 1
    assert sections[0].title == "<b>Section Title</b>"


def test_split_title_is_removed_from_content():
    # given
    html_content = """
    <body>
    <section>
        <h2>Section Title</h2>
        <p>This is the content of the section.</p>
    </section>
    </body>
    """
    semantic = WikipediaAPIContentSplitter()
    # when
    sections = semantic.split(html_content)
    # then
    assert len(sections) == 1
    assert sections[0].title == "Section Title"
    assert sections[0].content.strip() == "<p>This is the content of the section.</p>"


def test_split_sections_no_title_and_no_content():
    # given
    html_content = """
    <body>
        <section>
            <p id="mwBQ"></p>
        </section>
    </body>
    """
    semantic = WikipediaAPIContentSplitter()
    # when
    sections = semantic.split(html_content)
    # then
    assert len(sections) == 0


def test_split_preserve_hierarchy():
    # given
    html_content = """
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
    """
    semantic = WikipediaAPIContentSplitter()
    # when
    sections = semantic.split(html_content, flatten=False)

    # then
    assert len(sections) == 1
    assert sections[0].title == "Section 1"
    assert len(sections[0].children) == 2
    assert sections[0].children[0].title == "Nested Section 1.1"
    assert sections[0].children[1].title == "Nested Section 1.2"


def test_split_nested_sections_with_div():
    # given
    html_content = """
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
    """
    semantic = WikipediaAPIContentSplitter()
    # when
    sections = semantic.split(html_content, sections_tag_name="div", flatten=False)

    # then
    assert len(sections) == 1
    assert sections[0].title == "Section 1"
    assert len(sections[0].children) == 2
    assert sections[0].children[0].title == "Nested Section 1.1"
    assert sections[0].children[1].title == "Nested Section 1.2"


def test_split_complex_simplified_page(read_simplified_melies):
    """
    For example, this simplified page has a complex structure with nested sections.
    and also a section with a void title (no h2 tag)
    """
    # given
    semantic = WikipediaAPIContentSplitter()

    # when
    sections = semantic.split(read_simplified_melies)

    # then
    assert sections is not None
    assert len(sections) > 0
    assert "Pour les articles homonymes" in sections[0].content
    assert any(
        section.title == "Biographie" and len(section.children) > 0
        for section in sections
    ), "Should contain 'Jeunesse' section"
