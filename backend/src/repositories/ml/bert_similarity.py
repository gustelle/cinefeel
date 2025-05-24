from loguru import logger
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search

from src.interfaces.similarity import ISimilaritySearch
from src.settings import Settings


class SimilaritySearchError(Exception):
    """
    Custom exception for similarity search errors.
    """

    pass


class BertSimilaritySearch(ISimilaritySearch):
    """
    Class to handle BERT similarity calculations.
    """

    settings: Settings
    embedder: SentenceTransformer

    def __init__(self, settings: Settings):
        """
        Initialize the BERT similarity model.

        Args:
            model_name (str): The name of the BERT model to use.
        """
        self.settings = settings
        self.embedder = SentenceTransformer(settings.bert_model)

    def most_similar(self, query: str, corpus: list[str]) -> str | None:
        """
        Find the most similar phrase to the given query within the corpus using BERT embeddings.

        If the similarity score is below the threshold, None is returned.

        Example:
        ```python

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

            assert most_similar_section_title == "film"
        ```

        Args:
            query (str): the query string to find the most similar phrase for.
            corpus (list[str]): the list of phrases to search within.

        Raises:
            SimilaritySearchError:

        Returns:
            str | None: the most similar phrase from the corpus, or None if no similar phrase is found.
        """

        try:
            # see https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
            # to improve the performance of the semantic search
            # use to("cuda") if you have a GPU
            titles_embeddings = self.embedder.encode(corpus, convert_to_tensor=True)

            # score = section_title_query_result.points[0].score
            query_embedding = self.embedder.encode(query, convert_to_tensor=True)

            hits = semantic_search(
                query_embedding,
                titles_embeddings,
                top_k=1,
            )

            most_similar_section_title = corpus[hits[0][0]["corpus_id"]]
            score = hits[0][0]["score"]

            if score < self.settings.bert_similarity_threshold:
                logger.info(
                    f"no confidence for '{query}' (found '{most_similar_section_title}' with score {score})"
                )
                return None

            return most_similar_section_title

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise SimilaritySearchError(f"Error in BERT similarity search: {e}") from e
