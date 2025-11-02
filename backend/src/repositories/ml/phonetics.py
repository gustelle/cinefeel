from loguru import logger
from pyphonetics import Soundex

from src.interfaces.nlp_processor import Processor

from .exceptions import SimilaritySearchError


class PhoneticSearch(Processor[str]):

    corpus: list[str] = []

    def __init__(self, corpus: list[str]):

        self.corpus = corpus

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

            soundex = Soundex()

            sounds_like = [soundex.sounds_like(query, c) for c in self.corpus]

            first_match = next(
                (c for c, match in zip(self.corpus, sounds_like) if match), None
            )

            logger.debug(f"Phonetic search for '{query}' found: {first_match}")

            return first_match

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            raise SimilaritySearchError(f"Error in phonetic search: {e}") from e
