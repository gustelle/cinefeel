from src.entities.content import Section, TableOfContents


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


def test_TableOfContents_populate_by_name():

    # given

    selector = ".toc a"
    page_id = "Some_Page"
    entity_type = "Person"

    # when
    toc = TableOfContents(
        page_id=page_id, inner_links_selector=selector, entity_type=entity_type
    )

    # then
    assert toc.page_id == page_id
    assert toc.inner_links_selector == selector
    assert toc.entity_type == entity_type


def test_TableOfContents_populate_by_alias():

    # given

    selector = ".toc a"
    page_id = "Some_Page"
    entity_type = "Person"

    # when
    toc = TableOfContents(
        page_id=page_id, link_selector=selector, entity_type=entity_type
    )

    # then
    assert toc.page_id == page_id
    assert toc.inner_links_selector == selector
    assert toc.entity_type == entity_type
