from typing import Protocol

from src.entities.ml import ExtractionResult, FormattedResult


class ILLM(Protocol):
    """
    Interface for entity resolver classes.
    """

    def request_entity(self, *args, **kwargs) -> ExtractionResult:
        """requests the extraction of an entity from the LLM (e.g., a person, a film, etc.)."""

        raise NotImplementedError("Subclasses must implement this method.")

    def request_formatted(self, *args, **kwargs) -> FormattedResult:
        """requests the formatting of an entity from the LLM (e.g. a date)."""

        raise NotImplementedError("Subclasses must implement this method.")
