from src.entities.composable import Composable
from src.entities.content import Section
from src.repositories.html_parser.html_chopper import Html2TextSectionsChopper
from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
from src.repositories.html_parser.wikipedia_info_retriever import (
    INFOBOX_SECTION_TITLE,
    WikipediaParser,
)
from src.repositories.ml.bert_summary import SectionSummarizer
from src.repositories.ml.html_to_text import TextSectionConverter
from src.settings import Settings

from .stubs.stub_pruner import DoNothingPruner


def test_retrieve_infobox_is_processed_correctly(
    # given
    read_beethoven_html,
):
    """
    Test that the infobox is retrieved before the content simplification.
    This is important to ensure that the infobox data is available for further processing.
    """

    # given
    settings = Settings()
    retriever = WikipediaParser()

    text_converter = TextSectionConverter()
    section_summarizer = SectionSummarizer(settings=settings)

    analyzer = Html2TextSectionsChopper(
        content_splitter=WikipediaAPIContentSplitter(
            parser=retriever, pruner=DoNothingPruner()
        ),
        post_processors=[
            text_converter,
            section_summarizer,
        ],
    )

    content_id = "test_content_id"

    # when
    _, sections = analyzer.process(
        content_id=content_id, html_content=read_beethoven_html
    )

    # then
    assert sections is not None, "Result should not be None."
    assert any(section.title == INFOBOX_SECTION_TITLE for section in sections)


def test_process_complex_page(read_melies_html):
    """
    Test the process method of the HtmlChopper class with a complex HTML page.
    """

    # given
    settings = Settings()
    retriever = WikipediaParser()
    html_cleaner = TextSectionConverter()
    section_summarizer = SectionSummarizer(settings=settings)

    analyzer = Html2TextSectionsChopper(
        content_splitter=WikipediaAPIContentSplitter(
            parser=retriever, pruner=DoNothingPruner()
        ),
        post_processors=[
            html_cleaner,
            section_summarizer,
        ],
    )

    content_id = "test_content_id"

    # when
    result = analyzer.process(content_id=content_id, html_content=read_melies_html)

    # then
    assert result is not None, "Result should not be None."
    assert isinstance(result, tuple), "Result should be a tuple."
    assert isinstance(result[0], Composable), "First element should be Composable."
    assert isinstance(result[1], list), "Second element should be a list of sections."
    assert all(
        isinstance(section, Section) for section in result[1]
    ), "All sections should be of type Section."
    assert any(
        "Biographie" in section.title and len(section.children) > 0
        for section in result[1]
    ), "Should contain 'Jeunesse' section with children."
