import pytest

from src.repositories.html_parser.html_chopper import Html2TextSectionsChopper
from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.repositories.ml.bert_similarity import SimilarSectionSearch
from src.repositories.ml.bert_summary import SectionSummarizer
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.repositories.ml.html_to_text import TextSectionConverter
from src.repositories.ml.ollama_parser import OllamaExtractor
from src.repositories.resolver.person_resolver import BasicPersonResolver
from src.settings import Settings


@pytest.mark.skip(
    reason="requires OllamaExtractor and SimilarSectionSearch to be stubbed."
)
def test_e2e_BasicPersonResolver(read_melies_html):
    """TODO:
    - create a stub to simulate the OllamaExtractor and SimilarSectionSearch
    """

    # Given a person specifications and summary

    settings = Settings()

    analyzer = Html2TextSectionsChopper(
        content_splitter=WikipediaAPIContentSplitter(),
        html_retriever=WikipediaParser(),
        html_simplifier=HTMLSimplifier(),
        html_cleaner=TextSectionConverter(),
        section_summarizer=SectionSummarizer(settings=settings),
    )

    base_info, section = analyzer.process("1", read_melies_html)

    # when
    p = BasicPersonResolver(
        entity_extractor=OllamaExtractor(settings=settings),
        section_searcher=SimilarSectionSearch(settings=settings),
    ).resolve(
        base_info=base_info,
        sections=section,
    )

    # When resolving the person

    # Then the person should be correctly resolved
    print(p)
