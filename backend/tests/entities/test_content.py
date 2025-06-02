from src.entities.content import Section


def test_nested_sections():
    """
    Test that nested sections are correctly represented.
    """
    section = Section(
        title="Main Section",
        content="This is the main section.",
        children=[
            Section(title="Subsection 1", content="Content of subsection 1"),
            Section(title="Subsection 2", content="Content of subsection 2"),
        ],
    )

    assert section.title == "Main Section"
    assert section.content == "This is the main section."
    assert len(section.children) == 2
    assert section.children[0].title == "Subsection 1"
    assert section.children[1].title == "Subsection 2"
