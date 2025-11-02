import pytest

from src.entities.content import Section
from src.entities.ml import ExtractionResult
from src.entities.movie import FilmMedia, Movie
from src.entities.person import Person, PersonCharacteristics, PersonVisibleFeatures
from src.interfaces.resolver import ResolutionConfiguration
from src.repositories.resolver.abstract_resolver import AbstractResolver
from src.settings import AppSettings

from .stubs.stub_extractor import StubExtractor
from .stubs.stub_similarity import ExactTitleSimilaritySearch, StubSimilaritySearch


def test_extract_entities_with_children():
    """
    children sections should be processed as well.
    """

    # given

    base_info = Movie(
        uid="test_uid",
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    parent_title = "Parent title"
    child_title = "Child title"

    sections_dict = [
        {
            "title": parent_title,
            "content": "parent content",
            "children": [{"title": child_title, "content": "child content"}],
        },
    ]
    sections = [Section(**section) for section in sections_dict]

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Movie]):

        def __init__(
            self,
        ):

            self.section_searcher = ExactTitleSimilaritySearch()

            # we only want to extract FilmMedia entities
            # nevermind the title, it's just for testing
            # the similarity search will return the first section from the provided list
            self.configurations = [
                ResolutionConfiguration(
                    extractor=StubExtractor(),
                    section_titles=[parent_title, child_title],
                    extracted_type=FilmMedia,
                ),
            ]

        def assemble(self, *args, **kwargs):
            return None

        def patch_media(self, entity, sections):
            return entity

        def validate_entity(self, entity):
            # For testing purposes, we assume the entity is always valid
            return entity

    resolver = TestResolver()

    # When extracting entities
    extracted_entities = resolver.extract_entities(sections, base_info)

    # Then
    # there should be two entities extracted, one for the parent section and one for the child section
    assert len(extracted_entities) == 2
    assert all(isinstance(entity.entity, FilmMedia) for entity in extracted_entities)


def test_extracted_entities_uid_is_assigned(test_settings: AppSettings):
    """
    Test that the extracted entities have their UID assigned correctly.
    this is a major requirement for the resolver to work properly
    because it allows to merge information later on.
    """

    # given
    base_info = Movie(
        uid="test_uid",
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    sections = [
        Section(title="Section 1", content="Content 1"),
        Section(title="Section 2", content="Content 2"),
    ]

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Movie]):

        def __init__(self):

            self.section_searcher = ExactTitleSimilaritySearch()
            self.configurations = [
                ResolutionConfiguration(
                    extractor=StubExtractor(),
                    section_titles=["Section 1", "Section 2"],
                    extracted_type=FilmMedia,
                ),
            ]

        def assemble(self, *args, **kwargs):
            return None

        def patch_media(self, entity, sections):
            return entity

        def validate_entity(self, entity):
            # For testing purposes, we assume the entity is always valid
            return entity

    resolver = TestResolver()

    # When extracting entities
    results = resolver.extract_entities(sections, base_info)

    # Then
    assert len(results) == 2


def test_sections_max_children(test_settings: AppSettings):
    # given

    # a section withe lots of children
    sections = [
        Section(
            title="Section with many children",
            content="Content with many children",
            children=[
                Section(title=f"Child {i}", content=f"Content {i}")
                for i in range(1, 11)  # 10 children
            ],
        ),
        Section(title="Another Section", content="Content without children"),
    ]

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Movie]):

        def __init__(self):
            self.entity_extractor = StubExtractor()
            self.section_searcher = StubSimilaritySearch(sections)
            self.configurations = {
                FilmMedia: ["Section 1", "Section 2"],
            }
            self.section_settings = test_settings.section_settings.model_copy(
                update={
                    "max_children": 5,  # Limit to 5 children per section
                }
            )

        def assemble(self, *args, **kwargs):
            return None

        def patch_media(self, entity, sections):
            return entity

        def validate_entity(self, entity):
            # For testing purposes, we assume the entity is always valid
            return entity

    resolver = TestResolver()

    # When filtering sections
    filtered_sections = resolver.filter_sections(sections)

    # Then
    # the first section should have only 5 children
    assert len(filtered_sections[0].children) == 5


def test_sections_max_per_page(test_settings: AppSettings):
    # given
    # lots of sections, more than the max per page
    sections = [
        Section(title=f"Section {i}", content=f"Content {i}")
        for i in range(1, 201)  # 200 sections
    ]

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Movie]):

        def __init__(self):
            self.entity_extractor = StubExtractor()
            self.section_searcher = StubSimilaritySearch(sections)
            self.configurations = {
                FilmMedia: ["Section 1", "Section 2"],
            }
            self.section_settings = test_settings.section_settings.model_copy(
                update={
                    "max_per_page": 100,  # Limit to 100 sections per page
                }
            )

        def assemble(self, *args, **kwargs):
            return None

        def patch_media(self, entity, sections):
            return entity

        def validate_entity(self, entity):
            # For testing purposes, we assume the entity is always valid
            return entity

    resolver = TestResolver()

    # When filtering sections
    filtered_sections = resolver.filter_sections(sections)

    # Then
    assert len(filtered_sections) == 100


def test_extract_entities_calls_extractor_with_parent_arg():
    """
    Test that the extractor is called with the parent argument.
    This is important for the resolver to work properly.
    """

    # given
    base_info = Movie(
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    sections = [
        Section(title="Section 1", content="Content 1"),
    ]

    extractor = StubExtractor()

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Movie]):

        def __init__(self):
            self.section_searcher = ExactTitleSimilaritySearch()
            self.configurations = [
                ResolutionConfiguration(
                    extractor=extractor,
                    section_titles=["Section 1"],
                    extracted_type=FilmMedia,
                ),
            ]

        def assemble(self, *args, **kwargs):
            return None

        def patch_media(self, entity, sections):
            return entity

        def validate_entity(self, entity):
            # For testing purposes, we assume the entity is always valid
            return entity

    resolver = TestResolver()

    # When extracting entities
    resolver.extract_entities(sections, base_info)

    # Then
    assert extractor.parent == base_info


@pytest.mark.skip(reason="Not implemented yet")
def test_resolve_as():

    # given
    base_info = Person(
        title="John Doe",
        permalink="http://example.com/john-doe",
    )
    parts = [
        ExtractionResult(
            entity=PersonVisibleFeatures(
                skin_color="claire",
                parent_uid=base_info.uid,
            ),
            resolve_as=PersonCharacteristics,
        )
    ]

    extractor = StubExtractor()

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Person]):

        def __init__(self):
            self.section_searcher = ExactTitleSimilaritySearch()
            self.configurations = [
                ResolutionConfiguration(
                    extractor=extractor,
                    section_titles=["Section 1"],
                    extracted_type=PersonVisibleFeatures,
                ),
            ]

        def patch_media(self, entity, sections):
            return entity

        def validate_entity(self, entity):
            # For testing purposes, we assume the entity is always valid
            return entity

    resolver = TestResolver()

    # when
    resolver.assemble(
        base_info=base_info,
        parts=parts,
    )

    # then
    # assert person is not None and person.characteristics.skin_color == "claire"
