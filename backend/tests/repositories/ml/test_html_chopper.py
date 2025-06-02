from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.repositories.html_parser.html_chopper import HtmlChopper

from .stub.stub_pruner import StubPruner
from .stub.stub_retriever import (
    NoPermakinRetriever,
    NoTitleRetriever,
    StubHtmlRetriever,
)
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

    splitter = StubHtmlSplitter()
    retriever = StubHtmlRetriever(
        [Section(title="Test Infobox", content="Some content")]
    )
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()
    pruner = StubPruner()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
        html_simplifier=html_simplifier,
        html_pruner=pruner,
        summarizer=summarizer,
    )

    # when
    base_info, sections = analyzer.analyze(content_id, html_content)

    # then
    assert isinstance(base_info, SourcedContentBase)
    assert isinstance(sections, list)
    assert len(sections) > 0
    assert all(isinstance(section, Section) for section in sections)


def test_analyze_empty_html():
    # given
    content_id = "test_empty_html"
    html_content = ""

    splitter = StubHtmlSplitter()
    retriever = StubHtmlRetriever()
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()
    pruner = StubPruner()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
        html_simplifier=html_simplifier,
        html_pruner=pruner,
        summarizer=summarizer,
    )

    # when
    result = analyzer.analyze(content_id, html_content)

    # then
    assert result is None


def test_analyze_splitter_is_called():
    # given
    content_id = "test_no_sections"
    html_content = "<html><body>No sections here.</body></html>"

    splitter = StubHtmlSplitter()
    retriever = StubHtmlRetriever()
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()
    pruner = StubPruner()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
        html_simplifier=html_simplifier,
        html_pruner=pruner,
        summarizer=summarizer,
    )

    # when
    analyzer.analyze(content_id, html_content)

    # then
    assert splitter.is_called


def test_analyze_summarizer_is_called():
    # given
    content_id = "test_retriever_called"
    html_content = "<html><body>Content with infobox.</body></html>"

    splitter = StubHtmlSplitter()
    retriever = StubHtmlRetriever()
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()
    pruner = StubPruner()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
        html_simplifier=html_simplifier,
        html_pruner=pruner,
        summarizer=summarizer,
    )

    # when
    analyzer.analyze(content_id, html_content)

    # then
    assert summarizer.is_called


def test_analyze_simplifier_is_called():
    # given
    content_id = "test_simplifier_called"
    html_content = "<html><body>Content to be simplified.</body></html>"

    splitter = StubHtmlSplitter()
    retriever = StubHtmlRetriever()
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()
    pruner = StubPruner()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
        html_simplifier=html_simplifier,
        html_pruner=pruner,
        summarizer=summarizer,
    )

    # when
    analyzer.analyze(content_id, html_content)

    # then
    assert html_simplifier.is_called


def test_analyze_no_permalink_found():
    # given
    content_id = "test_no_permalink"
    html_content = "<html><body>No permalink here.</body></html>"

    splitter = StubHtmlSplitter()
    retriever = NoPermakinRetriever()
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()
    pruner = StubPruner()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
        html_simplifier=html_simplifier,
        html_pruner=pruner,
        summarizer=summarizer,
    )

    # when
    result = analyzer.analyze(content_id, html_content)

    # then
    assert result is None


def test_analyze_no_title_found():
    # given
    content_id = "test_no_title"
    html_content = "<html><body>No title here.</body></html>"

    splitter = StubHtmlSplitter()
    retriever = NoTitleRetriever()
    summarizer = StubSummarizer()
    html_simplifier = StubSimplifier()
    pruner = StubPruner()

    analyzer = HtmlChopper(
        html_splitter=splitter,
        html_retriever=retriever,
        html_simplifier=html_simplifier,
        html_pruner=pruner,
        summarizer=summarizer,
    )

    # when
    result = analyzer.analyze(content_id, html_content)

    # then
    assert result is None
