from src.entities.extraction import ExtractionResult
from src.entities.film import FilmActor, FilmMedia, FilmSpecifications, FilmSummary
from src.interfaces.extractor import IDataMiner


class StubExtractor(IDataMiner):
    """
    returns dummy data for testing purposes.
    """

    is_parsed: bool = False

    def extract_entity(
        self, content: str, entity_type, *args, **kwargs
    ) -> ExtractionResult:
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
            return ExtractionResult(
                score=1.0, entity=FilmActor(uid="1", nom_complet="John Doe")
            )
        elif entity_type == FilmMedia:
            # Simulate returning a FilmMedia with dummy data
            return ExtractionResult(
                score=1.0,
                entity=FilmMedia(
                    uid="1", url_bande_annonce="https://example.com/trailer.mp4"
                ),
            )
        elif entity_type == FilmSpecifications:
            # Simulate returning FilmSpecifications with dummy data
            return ExtractionResult(
                score=1.0,
                entity=FilmSpecifications(
                    uid="1",
                    title="The Great Film",
                ),
            )
        elif entity_type == FilmSummary:
            # Simulate returning a FilmSummary with dummy data
            return ExtractionResult(
                score=1.0,
                entity=FilmSummary(
                    uid="1",
                    contenu_resume="An epic tale of adventure and discovery.",
                ),
            )

        return None
