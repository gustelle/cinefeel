from src.entities.film import (
    Film,
    FilmActor,
    FilmMedia,
    FilmSpecifications,
    FilmSummary,
)
from src.interfaces.extractor import IContentExtractor


class StubExtractor(IContentExtractor):
    """
    returns dummy data for testing purposes.
    """

    is_parsed: bool = False

    def extract_entity(self, content: str, entity_type) -> Film:
        """
        Parse the given content and return a dictionary representation.

        Args:
            content (str): The content to parse.

        Returns:
            dict: A dictionary representation of the parsed content.
        """
        self.is_parsed = True

        if entity_type == FilmActor:
            # Simulate returning a FilmActor with dummy data
            return FilmActor(nom_complet="John Doe")
        elif entity_type == FilmMedia:
            # Simulate returning a FilmMedia with dummy data
            return FilmMedia(url_bande_annonce="https://example.com/trailer.mp4")
        elif entity_type == FilmSpecifications:
            # Simulate returning FilmSpecifications with dummy data
            return FilmSpecifications(title="Dummy Film")
        elif entity_type == FilmSummary:
            # Simulate returning a FilmSummary with dummy data
            return FilmSummary(
                contenu_resume="This is a great film about testing stubs."
            )

        return None
