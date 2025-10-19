from src.entities.movie import Movie
from src.repositories.orchestration.tasks.task_html_parsing import (
    do_analysis,
    execute_task,
)
from src.settings import Settings

from ..stubs.stub_analyzer import StubAnalyzer
from ..stubs.stub_section_search import StubSectionSearch
from ..stubs.stub_stats import StubStatsCollector
from ..stubs.stub_storage import StubStorage


def test_task_parser_entity_is_stored_when_parsed(test_settings: Settings):

    # given
    # mock do_analysis to return a Movie
    stub_storage = StubStorage()

    content_id = "test_content_id"
    content = "<html><body>Test Content</body></html>"

    # when
    execute_task.fn(
        content_id=content_id,
        content=content,
        settings=test_settings,
        entity_type=Movie,
        output_storage=stub_storage,
        analyzer=StubAnalyzer(),
        search_processor=StubSectionSearch(),
        stats_collector=StubStatsCollector(),
    )

    # then
    assert stub_storage.is_inserted, "Film was not inserted into the storage."


def test_task_parser_analyze(test_settings: Settings):
    # given

    analyzer = StubAnalyzer()
    section_searcher = StubSectionSearch()

    content_id = "test_content_id"
    html_content = "<html><body>Test Content</body></html>"

    # when
    result = do_analysis(
        content_id=content_id,
        html_content=html_content,
        settings=test_settings,
        entity_type=Movie,
        analyzer=analyzer,
        search_processor=section_searcher,
    )

    # then

    assert isinstance(result, Movie), "Result is not of type Film."
    assert analyzer.is_analyzed, "Analyzer was not called."
    assert section_searcher.is_called, "Section searcher was not called."
