import re

from loguru import logger
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search
from torch import Tensor

from src.interfaces.content_splitter import Section
from src.interfaces.nlp_processor import Processor
from src.settings import Settings


class SimilaritySearchError(Exception):
    """
    Custom exception for similarity search errors.
    """

    pass


class SimilarSectionSearch(Processor[Section]):
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
        self.embedder = SentenceTransformer(settings.bert_similarity_model)

    def _most_similar_text(self, query: str, corpus: list[str]) -> str | None:
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

            if len(corpus) == 0:
                logger.warning("empty corpus, skipping the similarity search")
                return None

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
                return None

            return most_similar_section_title

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise SimilaritySearchError(f"Error in BERT similarity search: {e}") from e

    def process(self, title: str, sections: list[Section]) -> Section | None:
        """
        Find the most similar `Section` to the given title within the list of sections.

        Args:
            title (str): The title to find the most similar section for.
            sections (list[Section]): The list of sections to search within.

        Returns:
            str | None: The most similar section title, or None if no similar title is found.
        """

        # special case for empty title
        if title is None or len(title.strip()) == 0:
            the_section = next(
                (
                    section
                    for section in sections
                    if (section.title is None or len(section.title.strip()) == 0)
                ),
                None,
            )
            return the_section

        _section_content = None

        most_similar_section_title = self._most_similar_text(
            query=title,
            corpus=[section.title for section in sections],
        )

        if most_similar_section_title is None:
            return None

        pattern = re.compile(rf"\s*{title}\s*", re.IGNORECASE)

        _similar_sec_contents = [
            section for section in sections if pattern.match(section.title)
        ]

        if len(_similar_sec_contents) == 0:
            return None

        _section_content = _similar_sec_contents[0]

        if (
            _section_content is None
            or _section_content.content is None
            or len(_section_content.content) == 0
        ):
            return None

        return Section(
            title=most_similar_section_title,
            content=_section_content.content,
            children=_section_content.children,
            media=_section_content.media,
        )


class SimilarValueSearch(Processor[str]):
    """
    Class to handle BERT similarity calculations for string values.
    """

    settings: Settings
    embedder: SentenceTransformer
    corpus: list[str]
    corpus_embeddings: Tensor

    def __init__(self, settings: Settings, corpus: list[str]):
        """
        Initialize the BERT similarity model.

        It's important to compute the embeddings for the corpus once during initialization
        to avoid recomputing them for each query, which can be computationally expensive.

        Args:
            settings (Settings): The settings object containing the model name.
            corpus (list[str]): The list of values to search within.
        """
        self.settings = settings
        self.embedder = SentenceTransformer(settings.bert_similarity_model)
        self.corpus = corpus
        self.corpus_embeddings = self.embedder.encode(corpus, convert_to_tensor=True)

    def process(self, query: str) -> str | None:
        """
        Find the most similar value to the given query within the corpus.

        Args:
            query (str): The query string to find the most similar value for.
            corpus (list[str]): The list of values to search within.

        Returns:
            str | None: The most similar value from the corpus, or None if no similar value is found.
        """

        try:

            query_embedding = self.embedder.encode(query, convert_to_tensor=True)

            hits = semantic_search(
                query_embedding,
                self.corpus_embeddings,
                top_k=1,
            )

            most_similar_value = self.corpus[hits[0][0]["corpus_id"]]
            score = hits[0][0]["score"]

            if score < self.settings.bert_similarity_threshold:
                return None

            return most_similar_value

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise SimilaritySearchError(f"Error in BERT similarity search: {e}") from e
