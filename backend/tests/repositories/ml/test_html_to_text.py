from src.entities.content import Section
from src.repositories.ml.html_to_text import HTML2TextConverter


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
