from src.entities.content import Media, Section
from src.repositories.ml.html_to_text import TextSectionConverter


def test_media_are_preserved_in_section():
    """
    Test that media are preserved in the section.
    """

    # given
    converter = TextSectionConverter()
    section = Section(
        title="Test Section",
        content="<p>This is a test section with media.</p>",
        children=[],
        media=[
            Media(
                uid="media:1234",
                src="https://example.com/image.jpg",
                media_type="image",
                caption="Test Image",
            )
        ],
    )

    # when
    converted_section = converter.process(section)
    # then
    assert converted_section.media is not None
    assert len(converted_section.media) == 1


def test_children_are_preserved_in_section():
    # given
    converter = TextSectionConverter()
    section = Section(
        title="Test Section",
        content="<p>This is a test section with children.</p>",
        children=[
            Section(title="Child Section 1", content="<p>Child 1 content</p>"),
            Section(title="Child Section 2", content="<p>Child 2 content</p>"),
        ],
        media=[],
    )
    # when
    converted_section = converter.process(section)
    # then
    assert converted_section.children is not None
    assert len(converted_section.children) == 2
