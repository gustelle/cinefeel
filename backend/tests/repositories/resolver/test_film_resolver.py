from src.entities.content import Section
from src.entities.source import SourcedContentBase
from src.repositories.resolver.film_resolver import BasicFilmResolver

from .stubs.stub_extractor import StubExtractor
from .stubs.stub_similarity import StubSimilaritySearch


def test_BasicFilmResolver_nominal_case():
    # Given a film specifications and summary
    title = "The Great Film"
    permalink = "https://example.com/the-great-film"
    uid = "12345"
    base_info = SourcedContentBase(title=title, permalink=permalink, uid=uid)

    sections = [
        Section(
            title="Données clés",
            content="Some key data about the film.",
        ),
    ]

    # make as if ollama extracted entities from the sections
    stub_extractor = StubExtractor()

    # this stub will return the first section
    stub_similarity = StubSimilaritySearch(sections=sections)

    resolver = BasicFilmResolver(
        entity_extractor=stub_extractor,
        section_searcher=stub_similarity,
    )

    # When resolving the film
    film = resolver.resolve(base_info=base_info, sections=sections)

    # Then the film should be correctly resolved
    assert film is not None
    assert film.uid == uid
    assert film.title == title
    assert str(film.permalink) == permalink
