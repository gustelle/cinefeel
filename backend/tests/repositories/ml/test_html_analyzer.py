import pytest

from src.entities.content import Section
from src.entities.film import Film
from src.repositories.html_parser.html_chopper import HtmlChopper

from .stub.stub_extractor import StubExtractor
from .stub.stub_retriever import StubHtmlRetriever
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

    # section_found = Section(
    #     title="Film Title", content="Some description about the film."
    # )

    entity_transformer = StubExtractor[Film](returned_entity=returned_entity)
    # similarity_search = StubSimilaritySearch([section_found])
    splitter = StubHtmlSplitter()
    retriever = StubHtmlRetriever(
        [Section(title="Test Infobox", content="Some content")]
    )
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
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
