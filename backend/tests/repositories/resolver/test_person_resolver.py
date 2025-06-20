import pytest

from src.entities.content import Section
from src.entities.person import Person
from src.repositories.html_parser.html_chopper import Html2TextSectionsChopper
from src.repositories.html_parser.html_splitter import WikipediaAPIContentSplitter
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.repositories.ml.bert_similarity import SimilarSectionSearch
from src.repositories.ml.bert_summary import SectionSummarizer
from src.repositories.ml.html_simplifier import HTMLSimplifier
from src.repositories.ml.html_to_text import TextSectionConverter
from src.repositories.ml.ollama_data_miner import OllamaDataMiner
from src.repositories.resolver.person_resolver import BasicPersonResolver
from src.settings import Settings
from tests.repositories.resolver.stubs.stub_extractor import StubExtractor
from tests.repositories.resolver.stubs.stub_similarity import StubSimilaritySearch


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
        entity_extractor=OllamaDataMiner(settings=settings),
        section_searcher=SimilarSectionSearch(settings=settings),
    ).resolve(
        base_info=base_info,
        sections=section,
    )

    # When resolving the person

    # Then the person should be correctly resolved
    print(p)


def test_resolve_person_patch_media():
    # Given a film with no media
    p = Person(
        uid="12345",
        title="The Great Person",
        permalink="https://example.com/the-great-person",
    )

    sections = [
        Section(
            title="Posters",
            content="Poster1.jpg, Poster2.jpg",
            media=[
                {
                    "src": "https://example.com/Poster1.jpg",
                    "media_type": "image",
                    "uid": "poster1",
                },
                {
                    "src": "https://example.com/Poster2.jpg",
                    "media_type": "image",
                    "uid": "poster2",
                },
            ],
        ),
        Section(
            title="Videos",
            content="Trailer.mp4, BehindTheScenes.mp4",
            media=[
                {
                    "src": "https://example.com/Trailer.mp4",
                    "media_type": "video",
                    "uid": "trailer",
                },
                {
                    "src": "https://example.com/BehindTheScenes.mp4",
                    "media_type": "video",
                    "uid": "behind_the_scenes",
                },
            ],
        ),
        Section(
            title="Audio",
            content="Soundtrack.mp3",
            media=[
                {
                    "src": "https://example.com/Soundtrack.mp3",
                    "media_type": "audio",
                    "uid": "soundtrack",
                },
            ],
        ),
        Section(
            title="Miscellaneous",
            content="Some other information.",
        ),
    ]

    # make as if ollama extracted entities from the sections
    stub_extractor = StubExtractor()

    # this stub will return the first section
    stub_similarity = StubSimilaritySearch(sections=sections)

    resolver = BasicPersonResolver(
        entity_extractor=stub_extractor,
        section_searcher=stub_similarity,
    )

    # When patching media
    patched_person = resolver.patch_media(p, sections)

    # Then the film should have media patched
    assert patched_person.media is not None
    assert len(patched_person.media.photos) == 2
    assert len(patched_person.media.other_medias) == 3

    # assert str(patched_film.media.posters[0]) == "https://example.com/Poster1.jpg"
    # assert str(patched_film.media.posters[1]) == "https://example.com/Poster2.jpg"
    # assert str(patched_film.media.other_media[0]) == "https://example.com/Trailer.mp4"
    # assert (
    #     str(patched_film.media.other_media[1])
    #     == "https://example.com/BehindTheScenes.mp4"
    # )
    # assert (
    #     str(patched_film.media.other_media[2]) == "https://example.com/Soundtrack.mp3"
    # )
