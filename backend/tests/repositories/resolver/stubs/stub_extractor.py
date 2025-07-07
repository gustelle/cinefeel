from src.entities.composable import Composable
from src.entities.content import Media
from src.entities.film import FilmActor, FilmMedia, FilmSpecifications, FilmSummary
from src.entities.ml import ExtractionResult
from src.interfaces.extractor import IDataMiner


class StubExtractor(IDataMiner):
    """
    returns dummy data for testing purposes.
    """

    is_parsed: bool = False
    parent: Composable | None = None

    def extract_entity(
        self,
        content: str,
        media: list[Media],
        entity_type,
        *args,
        parent: Composable | None = None,
        **kwargs
    ) -> ExtractionResult:
        """
        Parse the given content and return a dictionary representation.

        Args:
            content (str): The content to parse.

        Returns:
            dict: A dictionary representation of the parsed content.
        """
        self.is_parsed = True
        self.parent = parent

        if entity_type == FilmActor:
            # Simulate returning a FilmActor with dummy data
            return ExtractionResult(
                score=1.0,
                entity=FilmActor(uid="1", full_name=content, parent_uid="test_uid"),
            )
        elif entity_type == FilmMedia:
            # Simulate returning a FilmMedia with dummy data
            return ExtractionResult(
                score=1.0,
                entity=FilmMedia(
                    uid="1",
                    posters=["https://example.com/trailer.mp4"],
                    parent_uid="test_uid",
                ),
            )
        elif entity_type == FilmSpecifications:
            # Simulate returning FilmSpecifications with dummy data
            return ExtractionResult(
                score=1.0,
                entity=FilmSpecifications(
                    uid="1",
                    title=content,
                    parent_uid="test_uid",
                ),
            )
        elif entity_type == FilmSummary:
            # Simulate returning a FilmSummary with dummy data
            return ExtractionResult(
                score=1.0,
                entity=FilmSummary(
                    uid="1",
                    content=content,
                    parent_uid="test_uid",
                ),
            )

        return None
