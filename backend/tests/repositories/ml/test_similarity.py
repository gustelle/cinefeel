import pytest

from src.interfaces.content_splitter import Section
from src.repositories.ml.similarity import SimilarSectionSearch
from src.settings import AppSettings


@pytest.mark.parametrize(
    "input,expected",
    [
        ("film", "film"),
        ("cinema", "cinema"),
        ("personne", "personne"),
        ("française", "Français"),
        ("données clés", "Données clés"),
        ("fiche technique", "Fiche technique"),
    ],
)
def test_similarity_search(
    test_settings: AppSettings,
    input: str,
    expected: str,
):
    """
    Test the BERT similarity search.
    """

    # given

    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)
    corpus = [
        "film",
        "cinema",
        "personne",
        "Français",
        "Allemand",
        "Finlandais",
        "Données clés",
        "Biographie",
        "Synopsis",
        "Fiche technique",
        "Récompenses",
        "Biographie",
        "Introduction",
        "Distribution",
    ]

    # when
    most_similar_section_title = bert_similarity_search._most_similar_text(
        input, corpus
    )

    # then
    assert most_similar_section_title == expected


def test_similarity_most_similar_section(
    test_settings: AppSettings,
):
    """
    Test the most similar section method.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)

    # Define a title and sections
    title = "film"
    sections = [
        {"title": "film", "content": "This is a film."},
        {"title": "cinema", "content": "This is a cinema."},
        {"title": "personne", "content": "This is a person."},
    ]
    sections = [Section(**section) for section in sections]

    # Perform the similarity search
    most_similar_section = bert_similarity_search.process(title, sections)

    # Check that the most similar section is correct
    assert most_similar_section.title == "film"
    assert most_similar_section.content == "This is a film."


def test_similarity_most_similar_section_empty(test_settings: AppSettings):
    """
    Test the most similar section method with an empty list of sections.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)

    # Define a title and an empty list of sections
    title = "film"
    sections: list[Section] = []

    # Perform the similarity search
    most_similar_section = bert_similarity_search.process(title, sections)

    # Check that the most similar section is None
    assert most_similar_section is None


def test_similarity_most_similar_section_no_match(test_settings: AppSettings):
    """
    Test the most similar section method with no matching sections.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)

    # Define a title and sections with no match
    title = "nonexistent"
    sections = [
        {"title": "film", "content": "This is a film."},
        {"title": "cinema", "content": "This is a cinema."},
        {"title": "personne", "content": "This is a person."},
    ]
    sections = [Section(**section) for section in sections]

    # Perform the similarity search
    most_similar_section = bert_similarity_search.process(title, sections)

    # Check that the most similar section is None
    assert most_similar_section is None


def test_similarity_most_similar_section_with_empty_title(test_settings: AppSettings):
    # given
    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)

    title = ""
    sections = [
        {"title": "", "content": "This is a film."},
        {"title": "cinema", "content": "This is a cinema."},
        {"title": "personne", "content": "This is a person."},
    ]

    sections = [Section(**section) for section in sections]

    # when
    most_similar_section = bert_similarity_search.process(title, sections)

    # then
    assert most_similar_section is not None
    assert most_similar_section.title == ""
    assert most_similar_section.content == "This is a film."


def test_similarity_most_similar_section_with_title_none(test_settings: AppSettings):
    # given
    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)

    title = None
    sections = [
        {"title": "", "content": "This is a film."},
        {"title": "cinema", "content": "This is a cinema."},
        {"title": "personne", "content": "This is a person."},
    ]

    sections = [Section(**section) for section in sections]

    # when
    most_similar_section = bert_similarity_search.process(title, sections)

    # then
    assert most_similar_section is not None
    assert most_similar_section.title == ""
    assert most_similar_section.content == "This is a film."


def test_similarity_most_similar_section_children_are_returned_in_section(
    test_settings: AppSettings,
):
    """
    Test that the most similar section returns children sections.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)

    # Define a title and sections with children
    title = "film"
    sections = [
        {
            "title": "film",
            "content": "This is a film.",
            "children": [
                {"title": "director", "content": "Directed by John Doe."},
                {"title": "cast", "content": "Starring Jane Doe."},
            ],
        },
        {"title": "cinema", "content": "This is a cinema."},
        {"title": "personne", "content": "This is a person."},
    ]
    sections = [Section(**section) for section in sections]

    # Perform the similarity search
    most_similar_section = bert_similarity_search.process(title, sections)

    # Check that the most similar section is correct
    assert most_similar_section.title == "film"
    assert most_similar_section.content == "This is a film."
    assert len(most_similar_section.children) == 2
    assert most_similar_section.children[0].title == "director"
    assert most_similar_section.children[1].title == "cast"


def test_similarity_media_are_provided_in_similar_section(test_settings: AppSettings):
    """
    Test that media are preserved in the section.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(test_settings.ml_settings)

    # Define a title and sections with media
    title = "film"
    sections = [
        {
            "title": "film",
            "content": "This is a film.",
            "media": [
                {
                    "uid": "media:1234",
                    "src": "https://example.com/image.jpg",
                    "media_type": "image",
                    "caption": "Test Image",
                }
            ],
        },
        {"title": "cinema", "content": "This is a cinema."},
        {"title": "personne", "content": "This is a person."},
    ]
    sections = [Section(**section) for section in sections]

    # Perform the similarity search
    most_similar_section = bert_similarity_search.process(title, sections)

    # Check that the most similar section is correct
    assert most_similar_section.title == "film"
    assert most_similar_section.content == "This is a film."
    assert len(most_similar_section.media) == 1
