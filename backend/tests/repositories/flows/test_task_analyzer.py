from pydantic import HttpUrl

from src.entities.film import Film
from src.repositories.orchestration.tasks.task_html_parsing import HtmlEntityExtractor
from src.settings import Settings

from .stubs.stub_analyzer import StubAnalyzer
from .stubs.stub_section_search import StubSectionSearch
from .stubs.stub_storage import StubStorage


def test_task_store():

    # given
    stub_storage = StubStorage()
    flow_runner = HtmlEntityExtractor(
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


def test_task_analyze(test_db_settings: Settings):
    # given

    flow_runner = HtmlEntityExtractor(
        settings=test_db_settings,
        entity_type=Film,
    )
    analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

    content_id = "test_content_id"
    html_content = "<html><body>Test Content</body></html>"

    # when
    result = flow_runner.do_analysis(
        analyzer=analyzer,
        content_id=content_id,
        html_content=html_content,
        section_searcher=section_searcher,
    )

    # then

    assert isinstance(result, Film), "Result is not of type Film."
    assert analyzer.is_analyzed, "Analyzer was not called."
    assert section_searcher.is_called, "Section searcher was not called."
