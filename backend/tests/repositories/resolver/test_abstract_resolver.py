from src.entities.content import Section
from src.entities.film import Film, FilmMedia
from src.repositories.resolver.abstract_resolver import AbstractResolver

from .stubs.stub_extractor import StubExtractor
from .stubs.stub_similarity import StubSimilaritySearch


def test_extract_entities_with_children():
    """
    Test the extract_entities method with sections that have children.
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

            # this will generate dummy data for testing
            self.entity_extractor = StubExtractor()

            # this stub will return the first section from the given list
            self.section_searcher = StubSimilaritySearch(sections)

            # we only want to extract FilmMedia entities
            # nevermind the title, it's just for testing
            # the similarity search will return the first section from the provided list
            self.entity_to_sections = {
                FilmMedia: ["nevermind the bollocks"],
            }

        def assemble(self, *args, **kwargs):
            return None

    resolver = TestResolver()

    # When extracting entities
    extracted_entities = resolver.extract_entities(sections, base_info)

    # Then
    # there should be two entities extracted, one for the parent section and one for the child section
    assert len(extracted_entities) == 2
    assert all(isinstance(entity.entity, FilmMedia) for entity in extracted_entities)
