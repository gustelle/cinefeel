from pydantic import HttpUrl

from src.entities.film import Film
from src.repositories.flows.tasks.task_html_parsing import HtmlParsingFlow
from src.settings import Settings

from .stubs.stub_analyzer import StubAnalyzer
from .stubs.stub_storage import StubStorage


def test_task_store():

    # given
    stub_storage = StubStorage()
    flow_runner = HtmlParsingFlow(
        settings=None,  # Assuming settings are not needed for this test
        entity_type=Film,
    )
    entity = Film(
        title="Test Film",
        permalink=HttpUrl("http://example.com/test-film"),
        uid="test_film_id",
    )

    # when
    flow_runner.to_storage(stub_storage, entity)

    # then
    assert stub_storage.is_inserted, "Film was not inserted into the storage."


def test_task_analyze():
    # given
    flow_runner = HtmlParsingFlow(
        settings=Settings(),  # settings are not really needed for this test
        entity_type=Film,
    )
    analyzer = StubAnalyzer()

    content_id = "test_content_id"
    html_content = "<html><body>Test Content</body></html>"

    # when
    result = flow_runner.do_analysis(
        analyzer=analyzer,
        content_id=content_id,
        html_content=html_content,
    )

    # then

    assert isinstance(result, Film), "Result is not of type Film."
    assert analyzer.is_analyzed, "Analyzer was not called."
