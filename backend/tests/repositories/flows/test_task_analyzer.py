from pydantic import HttpUrl

from src.entities.film import Film
from src.entities.person import Person
from src.repositories.flows.task_analyzer import AnalysisFlow
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.settings import Settings

from .stubs.stub_analyzer import StubAnalyzer
from .stubs.stub_storage import StubStorage


def test_task_store():

    # given
    stub_storage = StubStorage()
    flow_runner = AnalysisFlow(
        settings=None,  # Assuming settings are not needed for this test
        entity_type=Film,
    )
    entity = Film(
        title="Test Film",
        permalink=HttpUrl("http://example.com/test-film"),
        uid="test_film_id",
    )

    # when
    flow_runner.store(stub_storage, entity)

    # then
    assert stub_storage.is_inserted, "Film was not inserted into the storage."


def test_task_analyze():
    # given
    flow_runner = AnalysisFlow(
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


# @pytest.mark.skip(reason="parties à mocker pour éviter les latences trop longues")
def test_e2e_do_analysis(read_melies_html):
    """verify with a real case that the analysis flow works as expected."""
    # given

    from src.repositories.html_parser.html_chopper import Html2TextSectionsChopper
    from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
    from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
    from src.repositories.ml.bert_summary import SectionSummarizer
    from src.repositories.ml.html_to_text import TextSectionConverter

    settings = Settings()

    analyzer = Html2TextSectionsChopper(
        content_splitter=WikipediaAPIContentSplitter(
            parser=WikipediaParser(),
            pruner=HTMLSimplifier(),
        ),
        post_processors=[SectionSummarizer(settings=settings), TextSectionConverter()],
    )

    content_id = "test_content_id"

    # when
    flow_runner = AnalysisFlow(
        settings=settings,
        entity_type=Person,
    )

    result = flow_runner.do_analysis(
        analyzer=analyzer,
        content_id=content_id,
        html_content=read_melies_html,
    )

    # then
    assert isinstance(result, Person), "Result is not of type Person."
