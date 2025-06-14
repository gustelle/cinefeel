from src.entities.content import Section
from src.repositories.ml.html_to_text import HTML2TextConverter


def test_simple_html_conversion():
    # given
    title = """<span id="Pi.C3.A8ces_.C2.AB_mineures_.C2.BB" typeof="mw:FallbackId"></span>Pièces «<span id="mwCGA" typeof="mw:DisplaySpace"> </span>mineures<span id="mwCGE" typeof="mw:DisplaySpace"> </span>»"""
    pruner = HTML2TextConverter()
    section = Section(title=title, content=title)

    # when
    new_section = pruner.process(section)

    # then
    assert new_section.title.strip() == "Pièces « mineures »"
    assert new_section.content.strip() == "Pièces « mineures »"


def test_html_is_removed():
    # given
    html_content = """
    <section>
        <h2>Section Title</h2>
        <p>This is the content of the section.</p>
        <div><span>Some HTML content</span></div>
    </section>
    """
    section = Section(title="<span>Test Section</span>", content=html_content)
    pruner = HTML2TextConverter()

    # when
    new_section = pruner.process(section)

    assert new_section.title.strip() == "Test Section"
    assert "<section>" not in new_section.content
    assert "<h2>" not in new_section.content
    assert "<p>" not in new_section.content
    assert "<div>" not in new_section.content


def test_empty_html_content():
    # given
    html_content = ""
    pruner = HTML2TextConverter()
    section = Section(title="<span>Test Section</span>", content=html_content)

    # when
    section = pruner.process(section)

    # then
    assert section.content.strip() == ""


def test_links_are_preserved():
    # given
    html_content = """
    <p>Check out this <a href="https://example.com">link</a>!</p>
    """
    section = Section(title="<span>Test Section</span>", content=html_content)
    pruner = HTML2TextConverter()

    # when
    section = pruner.process(section)

    # then
    assert "https://example.com" in section.content


def test_images_are_preserved():
    # given
    html_content = """
    <p>Here is an image: <img src="https://example.com/image.jpg" alt="Example Image"></p>
    """
    section = Section(title="<span>Test Section</span>", content=html_content)
    pruner = HTML2TextConverter()

    # when
    section = pruner.process(section)

    # then
    assert "https://example.com/image.jpg" in section.content


def test_tables_are_preserved():
    # given
    html_content = """
    <table>
        <tr>
            <td>Cell 1</td>
            <td>Cell 2</td>
        </tr>
    </table>
    """
    section = Section(title="<span>Test Section</span>", content=html_content)
    pruner = HTML2TextConverter()

    # when
    section = pruner.process(section)

    # then
    assert "Cell 1" in section.content
    assert "Cell 2" in section.content


def test_emphasis_is_ignored():
    # given
    html_content = """
    <p>This is <em>emphasized</em> text.</p>
    """
    section = Section(title="<span>Test Section</span>", content=html_content)
    pruner = HTML2TextConverter()

    # when
    section = pruner.process(section)

    # then
    assert section.content.strip() == "This is emphasized text."


def test_nested_sections():
    # given
    html_content = """
        <p>Content of parent section.</p>
    """

    child_html = """
        <p>Content of child section.</p>
    """

    section = Section(
        title="<span>Test Section</span>",
        content=html_content,
        children=[Section(title="<span>Child Section</span>", content=child_html)],
    )
    pruner = HTML2TextConverter()

    # when
    new_section = pruner.process(section)

    # then
    assert new_section.children[0].title.strip() == "Child Section"
    assert new_section.children[0].content.strip() == "Content of child section."
