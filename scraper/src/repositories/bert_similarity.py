from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search
from settings import Settings


class BertSimilaritySearch:
    """
    Class to handle BERT similarity calculations.
    """

    embedder: SentenceTransformer

    def __init__(self, settings: Settings = None):
        """
        Initialize the BERT similarity model.

        Args:
            model_name (str): The name of the BERT model to use.
        """
        self.embedder = SentenceTransformer("Lajavaness/sentence-camembert-base")

    def most_similar(self, query: str, corpus: list[str]) -> str:
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

        print(
            f"most similar doc of '{query}': {most_similar_section_title} with score {score}"
        )

        if score < 0.9:
            print(
                f"no confidence for '{query}' (found '{most_similar_section_title}' with score {score})"
            )
            return None

        return most_similar_section_title
