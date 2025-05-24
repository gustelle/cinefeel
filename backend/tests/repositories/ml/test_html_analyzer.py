from src.entities.film import Film
from src.repositories.ml.html_analyzer import HtmlContentAnalyzer

from .stub.stub_extractor import StubHtmlExtractor
from .stub.stub_similarity import StubSimilaritySearch
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

    entity_transformer = StubEntityTransformer()
    similarity_search = StubSimilaritySearch()
    splitter = StubHtmlSplitter()
    extractor = StubHtmlExtractor()

    analyzer = HtmlContentAnalyzer(
        entity_transformer=entity_transformer,
        title_matcher=similarity_search,
        html_splitter=splitter,
        html_extractor=extractor,
    )

    # when
    result = analyzer.analyze(html_content)

    # then
    assert result is not None
    assert isinstance(result, Film)
    assert entity_transformer.is_parsed is True
