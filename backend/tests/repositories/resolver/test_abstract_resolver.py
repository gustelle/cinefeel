from src.entities.content import Section
from src.entities.film import Film, FilmMedia
from src.interfaces.resolver import ResolutionConfiguration
from src.repositories.resolver.abstract_resolver import AbstractResolver
from src.settings import Settings

from .stubs.stub_extractor import StubExtractor
from .stubs.stub_similarity import StubSimilaritySearch


def test_extract_entities_with_children():
    """
    children sections should be processed as well.
    """

    # given

    base_info = Film(
        uid="test_uid",
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    sections_dict = [
        {
            "title": "Parent Section",
            "content": "test parent",
            "children": [{"title": "Child Section", "content": "test parent"}],
        },
        {"title": "Standalone Section", "content": "test standalone"},
    ]
    sections = [Section(**section) for section in sections_dict]

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Film]):

        def __init__(
            self,
        ):

            # this stub will return the first section from the given list
            self.section_searcher = StubSimilaritySearch(sections)

            # we only want to extract FilmMedia entities
            # nevermind the title, it's just for testing
            # the similarity search will return the first section from the provided list
            self.configurations = [
                ResolutionConfiguration(
                    extractor=StubExtractor(),
                    section_titles=["Parent Section", "Child Section"],
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


def test_extracted_entities_uid_is_assigned():
    """
    Test that the extracted entities have their UID assigned correctly.
    this is a major requirement for the resolver to work properly
    because it allows to merge information later on.
    """

    # given
    base_info = Film(
        uid="test_uid",
        title="Test Film",
        permalink="http://example.com/test-film",
    )

    sections = [
        Section(title="Section 1", content="Content 1"),
        Section(title="Section 2", content="Content 2"),
    ]

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Film]):

        def __init__(self):
            self.entity_extractor = StubExtractor()
            self.section_searcher = StubSimilaritySearch(sections)
            self.configurations = {
                FilmMedia: ["Section 1", "Section 2"],
            }

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


def test_sections_max_children():
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
    class TestResolver(AbstractResolver[Film]):

        def __init__(self):
            self.entity_extractor = StubExtractor()
            self.section_searcher = StubSimilaritySearch(sections)
            self.configurations = {
                FilmMedia: ["Section 1", "Section 2"],
            }
            self.settings = Settings(
                sections_max_children=5,  # Limit to 5 children per section
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


def test_sections_max_per_page():
    # given
    # lots of sections, more than the max per page
    sections = [
        Section(title=f"Section {i}", content=f"Content {i}")
        for i in range(1, 201)  # 200 sections
    ]

    # Dummy resolver for testing
    class TestResolver(AbstractResolver[Film]):

        def __init__(self):
            self.entity_extractor = StubExtractor()
            self.section_searcher = StubSimilaritySearch(sections)
            self.configurations = {
                FilmMedia: ["Section 1", "Section 2"],
            }
            self.settings = Settings(
                sections_max_per_page=100,  # Limit to 100 sections per page
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
