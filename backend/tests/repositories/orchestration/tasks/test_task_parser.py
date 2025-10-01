from pydantic import HttpUrl

from src.entities.movie import Movie
from src.repositories.orchestration.tasks.task_html_parsing import HtmlDataParserTask
from src.settings import Settings

from ..stubs.stub_analyzer import StubAnalyzer
from ..stubs.stub_section_search import StubSectionSearch
from ..stubs.stub_storage import StubStorage


def test_task_store(test_settings: Settings):

    # given
    stub_storage = StubStorage()
    flow_runner = HtmlDataParserTask(
        settings=test_settings,
        entity_type=Movie,
    )
    entity = Movie(
        title="Test Film",
        permalink=HttpUrl("http://example.com/test-film"),
        uid="test_film_id",
    )

    # when
    flow_runner.to_storage(stub_storage, entity)

    # then
    assert stub_storage.is_inserted, "Film was not inserted into the storage."


def test_task_analyze(test_settings: Settings):
    # given

    analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

    flow_runner = HtmlDataParserTask(
        settings=test_settings,
        entity_type=Movie,
        analyzer=analyzer,
        search_processor=section_searcher,
    )

    content_id = "test_content_id"
    html_content = "<html><body>Test Content</body></html>"

    # when
    result = flow_runner.do_analysis(
        content_id=content_id,
        html_content=html_content,
    )

    # then

    assert isinstance(result, Movie), "Result is not of type Film."
    assert analyzer.is_analyzed, "Analyzer was not called."
    assert section_searcher.is_called, "Section searcher was not called."
