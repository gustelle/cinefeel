from src.entities.composable import Composable
from src.entities.content import Section
from src.entities.film import Film, FilmSpecifications
from src.interfaces.resolver import ResolutionConfiguration
from src.repositories.resolver.film_resolver import BasicFilmResolver

from .stubs.stub_extractor import StubExtractor
from .stubs.stub_similarity import ExactTitleSimilaritySearch, StubSimilaritySearch


def test_BasicFilmResolver_nominal_case():
    # Given a film specifications and summary
    title = "The Great Film"
    permalink = "https://example.com/the-great-film"
    uid = "12345"
    base_info = Composable(title=title, permalink=permalink, uid=uid)

    sections = [
        Section(
            title="Données clés",
            content="Some key data about the film.",
        ),
    ]

    # make as if ollama extracted entities from the sections
    stub_extractor = StubExtractor()

    # this stub will return the first section
    stub_similarity = ExactTitleSimilaritySearch()

    resolver = BasicFilmResolver(
        section_searcher=stub_similarity,
        configurations=[
            # Extracting film specifications
            ResolutionConfiguration(
                extractor=stub_extractor,
                section_titles=["Données clés", "Fiche technique"],
                extracted_type=FilmSpecifications,
            ),
        ],
    )

    # When resolving the film
    film = resolver.resolve(base_info=base_info, sections=sections)

    # Then the film should be correctly resolved
    assert film is not None
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
    stub_similarity = ExactTitleSimilaritySearch()

    resolver = BasicFilmResolver(
        section_searcher=stub_similarity,
        configurations=[
            # Extracting film specifications
            ResolutionConfiguration(
                extractor=stub_extractor,
                section_titles=["Données clés", "Fiche technique"],
                extracted_type=FilmSpecifications,
            ),
        ],
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


def test_validate_iso_duration():
    # Given a film with a valid duration
    film = Film(
        title="The Great Film",
        permalink="https://example.com/the-great-film",
    )
    film.specifications = FilmSpecifications(
        parent_uid=film.uid,
        title="Specifications for The Great Film",
        duration="01:30:02",  # ISO 8601 duration format
    )

    resolver = BasicFilmResolver(
        section_searcher=StubSimilaritySearch(
            return_value=Section(title="Fiche technique", content="Some content")
        ),
        configurations=[
            ResolutionConfiguration(
                extractor=StubExtractor(),
                section_titles=["Fiche technique"],
                extracted_type=FilmSpecifications,
            ),
        ],
    )

    # When validating the duration
    film = resolver.validate_entity(film)

    # Then the duration should be valid
    assert film.specifications.duration == "01:30:02"


def test_validate_duration_by_regex_no_hour():
    # Given a film with an invalid duration
    film = Film(
        title="The Great Film",
        permalink="https://example.com/the-great-film",
    )
    film.specifications = FilmSpecifications(
        title="Specifications for The Great Film",
        duration="1 minute 20 secondes",  # Non-ISO duration format
        parent_uid=film.uid,
    )

    resolver = BasicFilmResolver(
        section_searcher=StubSimilaritySearch(
            return_value=Section(title="Fiche technique", content="Some content")
        ),
        configurations=[
            ResolutionConfiguration(
                extractor=StubExtractor(),
                section_titles=["Données clés", "Fiche technique"],
                extracted_type=FilmSpecifications,
            ),
        ],
    )

    # When validating the duration
    film = resolver.validate_entity(film)

    # Then the duration should be None or invalid
    assert (
        film.specifications.duration == "00:01:20"
    )  # Assuming the resolver converts it to a valid format


def test_validate_duration_by_regex_with_hour():
    # Given a film with an invalid duration
    film = Film(
        title="The Great Film",
        permalink="https://example.com/the-great-film",
    )
    film.specifications = FilmSpecifications(
        title="Specifications for The Great Film",
        duration="1 heure 20 minutes 30 secondes",  # Non-ISO duration format
        parent_uid=film.uid,
    )

    resolver = BasicFilmResolver(
        section_searcher=StubSimilaritySearch(
            return_value=Section(title="Fiche technique", content="Some content")
        ),
        configurations=[
            ResolutionConfiguration(
                extractor=StubExtractor(),
                section_titles=["Données clés", "Fiche technique"],
                extracted_type=FilmSpecifications,
            ),
        ],
    )

    # When validating the duration
    film = resolver.validate_entity(film)

    # Then the duration should be None or invalid
    assert (
        film.specifications.duration == "01:20:30"
    )  # Assuming the resolver converts it to a valid format
