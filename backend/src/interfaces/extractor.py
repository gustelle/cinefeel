from typing import Protocol, Sequence

from src.entities.component import EntityComponent
from src.entities.composable import Composable
from src.entities.content import Media
from src.entities.ml import ExtractionResult
from src.interfaces.llm import ILLM


class IDataMiner(ILLM, Protocol):
    """
    A data miner that extracts entities from a content
    """

    def extract_entity(
        self,
        content: str,
        media: Sequence[Media],
        entity_type: EntityComponent,
        parent: Composable | None = None,
        *args,
        **kwargs
    ) -> ExtractionResult:
        """
        Extract entity from the provided content.

        Args:
            content (str): The content from which to extract the entity.
            media (Sequence[Media]): A sequence of Media objects associated with the content.
            entity_type (Storable): The type of entity to extract, which should be a subclass of `Storable`.
            parent_content (Composable): Base information including the parent to which the entity belongs,
                leave it as `None` if the entity is not part of a larger context.
            *args: Additional positional arguments for the extraction process.
            **kwargs: Additional keyword arguments for the extraction process.

        Returns:
            ExtractionResult: The result of the extraction, containing the extracted entity and scoring (confidence) information.
        """
        raise NotImplementedError("Subclasses must implement this method.")
