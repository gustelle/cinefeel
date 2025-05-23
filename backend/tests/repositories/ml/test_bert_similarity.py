from src.repositories.ml.bert_similarity import BertSimilaritySearch
from src.settings import Settings


def test_bert_similarity_search():
    """
    Test the BERT similarity search.
    """

    # given
    # Initialize the BERT similarity search
    bert_similarity_search = BertSimilaritySearch(Settings())

    # Define a query and a corpus
    query = "film"
    corpus = [
        "film",
        "cinema",
        "personne",
    ]

    # Perform the similarity search
    most_similar_section_title = bert_similarity_search.most_similar(query, corpus)

    # Check that the most similar section title is correct
    assert most_similar_section_title == "film"
