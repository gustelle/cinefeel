from src.entities.nationality import NATIONALITIES
from src.repositories.ml.phonetics import PhoneticSearch
from src.settings import AppSettings


def test_phonetics_similar_nationality_search(test_settings: AppSettings):
    """
    Test the SimilaritySearch for nationalities.
    """

    # given
    similar_value_search = PhoneticSearch(NATIONALITIES["FR"])

    # Define a query
    query = "francaise"

    # Perform the similarity search
    most_similar_value = similar_value_search.process(query)

    # Check that the most similar value is correct
    assert most_similar_value == "français"
