from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.settings import Settings


def test_retrieve_infobox_is_processed_correctly(
    read_beethoven_html,
):
    """
    Test that the infobox is retrieved before the content simplification.
    This is important to ensure that the infobox data is available for further processing.
    """
    from src.repositories.html_parser.html_chopper import HtmlChopper
    from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
    from src.repositories.html_parser.wikipedia_info_retriever import (
        WikipediaInfoRetriever,
    )
    from src.repositories.ml.bert_summary import SectionSummarizer
    from src.repositories.ml.html_simplifier import HTMLSimplifier
    from src.repositories.ml.html_to_text import HTML2TextConverter

    # given
    settings = Settings()

    analyzer = HtmlChopper(
        html_splitter=WikipediaAPIContentSplitter(),
        html_retriever=WikipediaInfoRetriever(),
        html_simplifier=HTMLSimplifier(),
        html_pruner=HTML2TextConverter(),
        summarizer=SectionSummarizer(settings=settings),
    )

    content_id = "test_content_id"

    # when
    result = analyzer.process(content_id=content_id, html_content=read_beethoven_html)

    # then
    assert result is not None, "Result should not be None."
    assert any(section.title == "Données clés" for section in result[1])


def test_process_complex_page(read_melies_html):
    """
    Test the process method of the HtmlChopper class with a complex HTML page.
    """
    from src.repositories.html_parser.html_chopper import HtmlChopper
    from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
    from src.repositories.html_parser.wikipedia_info_retriever import (
        WikipediaInfoRetriever,
    )
    from src.repositories.ml.bert_summary import SectionSummarizer
    from src.repositories.ml.html_simplifier import HTMLSimplifier
    from src.repositories.ml.html_to_text import HTML2TextConverter

    # given
    settings = Settings()

    analyzer = HtmlChopper(
        html_splitter=WikipediaAPIContentSplitter(),
        html_retriever=WikipediaInfoRetriever(),
        html_simplifier=HTMLSimplifier(),
        html_pruner=HTML2TextConverter(),
        summarizer=SectionSummarizer(settings=settings),
    )

    content_id = "test_content_id"

    # when
    result = analyzer.process(content_id=content_id, html_content=read_melies_html)

    # then
    assert result is not None, "Result should not be None."
    assert isinstance(result, tuple), "Result should be a tuple."
    assert isinstance(
        result[0], SourcedContentBase
    ), "First element should be SourcedContentBase."
    assert isinstance(result[1], list), "Second element should be a list of sections."
    assert all(
        isinstance(section, Section) for section in result[1]
    ), "All sections should be of type Section."
    assert any(
        "Biographie" in section.title and len(section.children) > 0
        for section in result[1]
    ), "Should contain 'Jeunesse' section with children."
