from typing import Protocol

from src.entities.content import Section
from src.entities.source import BaseInfo


class IEntityResolver[T](Protocol):
    """
    Interface for an entity assembler that transforms content into a specific entity type.
    """

    def resolve(
        self, uid: str, base_info: BaseInfo, sections: list[Section], *args, **kwargs
    ) -> T:
        """
        Resolves a list of parts into an entity of type T.

        Args:
            uid (str): A unique identifier for the entity being resolved.
            parts (list[BaseModel]): A list of BaseModel instances that represent the content to be resolved.
                Each part should conform to the structure defined by the entity type T.
        """
        pass
