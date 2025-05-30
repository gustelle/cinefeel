from typing import Protocol

from pydantic import BaseModel


class IEntityAssembler[T](Protocol):
    """
    Interface for an entity assembler that transforms content into a specific entity type.
    """

    def assembler(self, parts: list[BaseModel]) -> T:
        """
        Transform the given content into an entity of type T.

        Args:
            parts (list[BaseModel]): A list of BaseModel instances that represent the content to be assembled.
                Each part should conform to the structure defined by the entity type T.

        Returns:
            T: An instance of the entity type T, populated with data extracted from the content.

        Raises:
            ValueError: If the content cannot be parsed into an entity of type T.
        """
        pass
