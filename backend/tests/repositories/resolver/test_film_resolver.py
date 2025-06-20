from src.entities.content import Section
from src.entities.film import Film
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
    assert uid in film.uid
    assert film.title == title
    assert str(film.permalink) == permalink


def test_resolve_film_patch_media():
    # Given a film with no media
    film = Film(
        uid="12345",
        title="The Great Film",
        permalink="https://example.com/the-great-film",
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

    resolver = BasicFilmResolver(
        entity_extractor=stub_extractor,
        section_searcher=stub_similarity,
    )

    # When patching media
    patched_film = resolver.patch_media(film, sections)

    # Then the film should have media patched
    assert patched_film.media is not None
    assert len(patched_film.media.posters) == 2
    assert len(patched_film.media.trailers) == 2
    assert len(patched_film.media.other_medias) == 1
    assert str(patched_film.media.posters[0]) == "https://example.com/Poster1.jpg"
    assert str(patched_film.media.trailers[0]) == "https://example.com/Trailer.mp4"
    assert (
        str(patched_film.media.other_medias[0]) == "https://example.com/Soundtrack.mp3"
    )
