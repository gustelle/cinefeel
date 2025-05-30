import pytest

from src.entities.content import Section
from src.entities.film import Film
from src.repositories.html_parser.html_analyzer import HtmlContentAnalyzer

from .stub.stub_extractor import StubHtmlExtractor
from .stub.stub_parser import StubContentParser
from .stub.stub_similarity import StubSimilaritySearch
from .stub.stub_simplifier import StubSimplifier
from .stub.stub_splitter import StubHtmlSplitter
from .stub.stub_summarizer import StubSummarizer


def test_analyze_nominal_case():
    # given

    content_id = "test_film_id"

    html_content = """
    <html>
        <head>
            <title>Test Film</title>
        </head>
        <body>
            <h1>Film Title</h1>
            <p>Some description about the film.</p>
            <div class="wikitable">
                <table>
                    <tr>
                        <td>Film 1</td>
                        <td>Director 1</td>
                    </tr>
                    <tr>
                        <td>Film 2</td>
                        <td>Director 2</td>
                    </tr>
                </table>
            </div>
        </body>
    </html>
    """

    returned_entity = Film(
        title="Test Film",
        uid=content_id,
        description="Some description about the film.",
    )

    section_found = Section(
        title="Film Title", content="Some description about the film."
    )

    entity_transformer = StubContentParser[Film](returned_entity=returned_entity)
    similarity_search = StubSimilaritySearch([section_found])
    splitter = StubHtmlSplitter()
    extractor = StubHtmlExtractor(
        [Section(title="Test Infobox", content="Some content")]
    )
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()

    analyzer = HtmlContentAnalyzer[Film](
        content_parser=entity_transformer,
        section_searcher=similarity_search,
        html_splitter=splitter,
        html_extractor=extractor,
        html_simplifier=html_simplifier,
        summarizer=summarizer,
    )

    # when
    result = analyzer.analyze(content_id, html_content)

    # then
    assert isinstance(result, Film)
    assert entity_transformer.is_parsed is True
    assert summarizer.is_called is True
    assert splitter.is_called is True
    assert result.uid == returned_entity.uid  # Ensure the content ID is set correctly


@pytest.mark.skip(reason="Test not implemented yet")
def test_resolve_from_infobox():
    """verify the infobox is used to resolve the entity"""
    pass


@pytest.mark.skip(reason="Test not implemented yet")
def test_resolve_no_sections_no_infobox():
    """case when no sections and no infobox are found"""

    pass
