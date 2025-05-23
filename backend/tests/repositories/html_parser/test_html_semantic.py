from pathlib import Path

from src.repositories.html_parser.html_semantic import (
    HtmlSection,
    HtmlSemantic,
)

current_dir = Path(__file__).parent


def test_split_sections():
    """
    Test the split_sections method of the HtmlSemantic class.
    """
    # given
    html_file = current_dir / "wikipedia_html/Beethoven.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = HtmlSemantic()

    # when
    sections = semantic.split_sections(html_content)

    # then
    assert sections is not None
    assert len(sections) > 0
    assert all(
        isinstance(section, HtmlSection) for section in sections
    ), "All sections should be of type HtmlSection"


def test_split_sections_example():

    # given
    html_file = current_dir / "test_html/example.html"
    html_content = html_file.read_text(encoding="utf-8")

    semantic = HtmlSemantic()

    # when
    sections = semantic.split_sections(html_content)

    # then
    assert any("Sommaire" == section.title for section in sections)
    assert all(section.title != "Notes et références" for section in sections)
    assert all(section.title != "Voir aussi" for section in sections)
    assert all(section.title != "Voir aussi" for section in sections)

    html_content = list(
        filter(
            lambda section: section.title == "Sommaire",
            sections,
        )
    )[0]
    assert "figcaption" not in html_content


def test_split_sections_with_identifier():
    pass


def test_split_sections_no_title():
    pass


def test_split_sections_void_section():
    pass
