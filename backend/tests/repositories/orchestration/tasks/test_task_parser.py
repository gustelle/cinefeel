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
    runner = HtmlDataParserTask(
        settings=test_settings,
        entity_type=Movie,
    )
    entity = Movie(
        title="Test Film",
        permalink=HttpUrl("http://example.com/test-film"),
        uid="test_film_id",
    )

    # when
    runner.to_storage(stub_storage, entity)

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


# @flow
# def demo_flow(
#     test_settings: Settings,
# ):
#     analyzer = StubAnalyzer()
#     section_searcher = StubSectionSearch()

#     task_runner = HtmlDataParserTask(
#         settings=test_settings,
#         entity_type=Movie,
#         analyzer=analyzer,
#         search_processor=section_searcher,
#     )

#     entity = Movie(
#         title="Test Film",
#         permalink=HttpUrl("http://example.com/test-film"),
#         uid="test_film_id",
#     )

#     storage = RedisJsonStorage[Movie](settings=test_settings)

#     return task_runner.to_storage.with_options(
#         cache_policy=CACHE_POLICY, cache_key_fn=custom_cache_key_fn
#     ).submit(storage, entity, return_state=True)


# def test_task_to_storage_is_cacheable(test_settings: Settings):
#     # given

#     # when
#     result = demo_flow(test_settings=test_settings)
#     assert result.name == "Completed"

#     other_state = demo_flow(test_settings=test_settings)
#     assert other_state.name == "Cached"
#     assert result.result() == other_state.result()
