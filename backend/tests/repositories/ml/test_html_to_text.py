from src.entities.content import Section
from src.repositories.ml.html_to_text import TextSectionConverter


def test_simple_html_conversion():
    # given
    title = """<span id="Pi.C3.A8ces_.C2.AB_mineures_.C2.BB" typeof="mw:FallbackId"></span>Pièces «<span id="mwCGA" typeof="mw:DisplaySpace"> </span>mineures<span id="mwCGE" typeof="mw:DisplaySpace"> </span>»"""
    pruner = TextSectionConverter()
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
    pruner = TextSectionConverter()

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
    pruner = TextSectionConverter()
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
    pruner = TextSectionConverter()

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
    pruner = TextSectionConverter()

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
    pruner = TextSectionConverter()

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
    pruner = TextSectionConverter()

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
    pruner = TextSectionConverter()

    # when
    new_section = pruner.process(section)

    # then
    assert new_section.children[0].title.strip() == "Child Section"
    assert new_section.children[0].content.strip() == "Content of child section."


def test_sticked_tags_are_spaced():
    # given
    html_content = """1802-1812: la période<i id="mwAaw">Héroïque</i>"""
    html_title = html_content

    section = Section(title=html_title, content=html_content)
    pruner = TextSectionConverter()

    # when
    section = pruner.process(section)

    # then
    assert section.content.strip() == "1802-1812: la période Héroïque"
    assert section.title.strip() == "1802-1812: la période Héroïque"


def test_sticked_tags_are_spaced_within_children():
    # given
    html_content = """1802-1812: la période<i id="mwAaw">Héroïque</i>"""
    html_title = html_content

    section = Section(
        title=html_title,
        content=html_content,
        children=[Section(title=html_title, content=html_content)],
    )
    pruner = TextSectionConverter()

    # when
    section = pruner.process(section)

    # then
    assert section.content.strip() == "1802-1812: la période Héroïque"
    assert section.title.strip() == "1802-1812: la période Héroïque"
    assert section.children[0].content.strip() == "1802-1812: la période Héroïque"
    assert section.children[0].title.strip() == "1802-1812: la période Héroïque"


def test_transformation_is_idempotent():
    # given
    html_content = """1802-1812: la période<i id="mwAaw">Héroïque</i>"""
    html_title = html_content

    section = Section(title=html_title, content=html_content)
    pruner = TextSectionConverter()

    # when
    section1 = pruner.process(section)
    section2 = pruner.process(section1)

    # then
    assert section1.content == section2.content
    assert section1.title == section2.title
    assert section1.children == section2.children


def test_transformation_does_not_impact_future_transformations():
    # given
    html_content_1 = """<span id="Le_mythe_beethov.C3.A9nien" typeof="mw:FallbackId"></span>Le<i id="mwBE4">mythe</i>beethovénien"""
    html_title_1 = html_content_1

    html_content_2 = """<span id="L.E2.80.99.C5.93uvre_de_Beethoven" typeof="mw:FallbackId"></span>L’œuvre de Beethoven"""
    html_title_2 = html_content_2

    section_1 = Section(title=html_title_1, content=html_content_1)
    section_2 = Section(title=html_title_2, content=html_content_2)
    pruner = TextSectionConverter()

    # when
    section1 = pruner.process(section_1)
    section2 = pruner.process(section_2)

    # then
    assert section1.content.strip() == "Le mythe beethovénien"
    assert section1.title == "Le mythe beethovénien"
    assert section2.content.strip() == "L’œuvre de Beethoven"
    assert section2.title.strip() == "L’œuvre de Beethoven"
