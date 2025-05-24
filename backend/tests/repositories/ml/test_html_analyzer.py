from src.entities.content import InfoBoxElement, Section
from src.entities.film import Film
from src.repositories.ml.html_analyzer import HtmlContentAnalyzer

from .stub.stub_extractor import StubHtmlExtractor
from .stub.stub_similarity import Return1stSearch
from .stub.stub_splitter import StubHtmlSplitter
from .stub.stub_transformer import StubEntityTransformer


def test_html_analyzer():
    # given

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

    section_found = Section(
        title="Film Title", content="Some description about the film."
    )

    entity_transformer = StubEntityTransformer()
    similarity_search = Return1stSearch([section_found])
    splitter = StubHtmlSplitter()
    extractor = StubHtmlExtractor(
        [InfoBoxElement(title="Test Infobox", content="Some content")]
    )

    analyzer = HtmlContentAnalyzer(
        entity_transformer=entity_transformer,
        section_searcher=similarity_search,
        html_splitter=splitter,
        html_extractor=extractor,
    )

    # when
    result = analyzer.analyze(html_content)

    # then
    assert result is not None
    assert isinstance(result, Film)
    assert entity_transformer.is_parsed is True


def test_html_analyzer_from_infobox():
    """case when the film is extracted from the infobox, not from the section"""

    # given
    html_content = """
    <html>
        <head>
            <title>Test Film</title>
        </head>
        <body>
            <div class="infobox">
                <table>
                    <tr>
                        <th>Title</th>
                        <td>Film Title</td>
                    </tr>
                    <tr>
                        <th>Director</th>
                        <td>Director Name</td>
                    </tr>
                </table>
            </div>
        </body>
    </html>
    """

    entity_transformer = StubEntityTransformer()
    similarity_search = Return1stSearch([])
    splitter = StubHtmlSplitter()
    extractor = StubHtmlExtractor(
        [InfoBoxElement(title="Test Infobox", content="Some content")]
    )

    analyzer = HtmlContentAnalyzer(
        entity_transformer=entity_transformer,
        section_searcher=similarity_search,
        html_splitter=splitter,
        html_extractor=extractor,
    )

    # when
    result = analyzer.analyze(html_content)

    # then
    assert result is not None
    assert isinstance(result, Film)
    assert entity_transformer.is_parsed is True


def test_html_analyzer_no_sections_no_infobox():
    """case when no sections and no infobox are found"""

    # given
    html_content = "<html><body>No relevant content here.</body></html>"

    entity_transformer = StubEntityTransformer()
    similarity_search = Return1stSearch([])
    splitter = StubHtmlSplitter()
    extractor = StubHtmlExtractor([])

    analyzer = HtmlContentAnalyzer(
        entity_transformer=entity_transformer,
        section_searcher=similarity_search,
        html_splitter=splitter,
        html_extractor=extractor,
    )

    # when
    result = analyzer.analyze(html_content)

    # then
    assert result is None
    assert entity_transformer.is_parsed is False
