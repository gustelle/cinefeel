from src.interfaces.content_splitter import Section
from src.repositories.ml.bert_similarity import SimilarSectionSearch
from src.settings import Settings


def test_bert_similarity_search():
    """
    Test the BERT similarity search.
    """

    # given
    # Initialize the BERT similarity search
    bert_similarity_search = SimilarSectionSearch(Settings())

    # Define a query and a corpus
    query = "film"
    corpus = [
        "film",
        "cinema",
        "personne",
    ]

    # Perform the similarity search
    most_similar_section_title = bert_similarity_search._most_similar_text(
        query, corpus
    )

    # Check that the most similar section title is correct
    assert most_similar_section_title == "film"


def test_most_similar_section():
    """
    Test the most similar section method.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(Settings())

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


def test_most_similar_section_empty():
    """
    Test the most similar section method with an empty list of sections.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(Settings())

    # Define a title and an empty list of sections
    title = "film"
    sections: list[Section] = []

    # Perform the similarity search
    most_similar_section = bert_similarity_search.process(title, sections)

    # Check that the most similar section is None
    assert most_similar_section is None


def test_most_similar_section_no_match():
    """
    Test the most similar section method with no matching sections.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(Settings())

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


def test_most_similar_section_with_empty_title():
    # given
    bert_similarity_search = SimilarSectionSearch(Settings())

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


def test_most_similar_section_with_title_none():
    # given
    bert_similarity_search = SimilarSectionSearch(Settings())

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


def test_most_similar_section_children_are_returned_in_section():
    """
    Test that the most similar section returns children sections.
    """

    # given
    bert_similarity_search = SimilarSectionSearch(Settings())

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
