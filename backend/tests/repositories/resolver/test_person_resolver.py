import pytest

from src.entities.content import Section
from src.entities.person import Biography, Person
from src.interfaces.resolver import ResolutionConfiguration
from src.repositories.resolver.person_resolver import PersonResolver
from src.settings import AppSettings
from tests.repositories.resolver.stubs.stub_extractor import StubExtractor
from tests.repositories.resolver.stubs.stub_similarity import StubSimilaritySearch


def test_resolve_person_patch_media(
    test_settings: AppSettings,
):
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
    stub_similarity = StubSimilaritySearch(return_value=sections[0])

    resolver = PersonResolver(
        section_searcher=stub_similarity,
        configurations=[
            ResolutionConfiguration(
                extractor=stub_extractor,
                section_titles=["Posters", "Videos", "Audio", "Miscellaneous"],
                extracted_type=Person,
            ),
        ],
        settings=test_settings.section_settings,
    )

    # When patching media
    patched_person = resolver.patch_media(p, sections)

    # Then the film should have media patched
    assert patched_person.media is not None
    assert len(patched_person.media.photos) == 2
    assert len(patched_person.media.other_medias) == 3


def test_resolve_person_validate_nationalities(
    test_settings: AppSettings,
):
    # Given a person with valid nationalities
    p = Person(
        title="The Great Person",
        permalink="https://example.com/the-great-person",
    )
    p.biography = Biography(
        full_name="John Doe",
        nationalities=["Française", "Francais"],  # Valid nationalities
        parent_uid=p.uid,
    )

    resolver = PersonResolver(
        section_searcher=StubSimilaritySearch(
            return_value=Section(title="Biography", content="")
        ),
        configurations=[
            ResolutionConfiguration(
                extractor=StubExtractor(),
                section_titles=["Biography"],
                extracted_type=Biography,
            ),
        ],
        settings=test_settings.section_settings,
    )

    # When validating the person
    p = resolver.validate_entity(p)

    # Then the person should be valid
    assert p is not None
    assert p.biography.nationalities == ["français"]


@pytest.mark.skip(reason="requires Ollama to be running")
def test_resolve_person_validate_birth_date(
    test_settings: AppSettings,
):
    # Given a person with a valid birth date
    p = Person(
        title="The Great Person",
        permalink="https://example.com/the-great-person",
    )
    p.uid = Biography(
        uid="bio_12345",
        full_name="John Doe",
        birth_date="28 décembre 1861 à Paris",  # Valid date
    )
    resolver = PersonResolver(
        section_searcher=StubSimilaritySearch(
            return_value=Section(title="Biography", content="")
        ),
        configurations=[
            ResolutionConfiguration(
                extractor=StubExtractor(),
                section_titles=["Biography"],
                extracted_type=Biography,
            ),
        ],
        settings=test_settings.section_settings,
    )

    # When validating the person
    p = resolver.validate_entity(p)

    # Then the person should be valid
    assert p is not None
    assert p.biography.birth_date == "1861-12-28"


def test_resolve_person_validate_entity(
    test_settings: AppSettings,
):
    # Given a person with valid nationalities
    p = Person(
        title="The Great Person",
        permalink="https://example.com/the-great-person",
    )

    resolver = PersonResolver(
        section_searcher=StubSimilaritySearch(
            return_value=Section(title="Biography", content="")
        ),
        configurations=[
            ResolutionConfiguration(
                extractor=StubExtractor(),
                section_titles=["Biography"],
                extracted_type=Biography,
            ),
        ],
        settings=test_settings.section_settings,
    )

    # When validating the person
    p = resolver.validate_entity(p)

    # Then the person should be valid
    assert p.biography is not None
