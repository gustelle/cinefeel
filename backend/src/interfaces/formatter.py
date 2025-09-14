from typing import Protocol

from src.interfaces.llm import ILLM


class IFormatter(ILLM, Protocol):
    """A formatter that prepares content for extraction."""

    def format(self, content: str) -> str:
        """
        Format the content before extraction.

        Args:
            content (str): The content to format.

        Returns:
            str: The formatted content.
        """
        raise NotImplementedError("Subclasses must implement this method.")
