from typing import Sequence

from loguru import logger
from neo4j import GraphDatabase
from pydantic import validate_call
from pydantic_settings import BaseSettings

from src.entities.composable import Composable
from src.entities.film import Film
from src.interfaces.relation_manager import (
    IRelationshipHandler,
    Relationship,
    RelationshipType,
)
from src.interfaces.storage import IStorageHandler, StorageError
from src.settings import Settings


class AbstractMemGraph[T: Composable](IStorageHandler[T], IRelationshipHandler[T]):

    client: GraphDatabase
    settings: Settings
    entity_type: type[T]
    _is_initialized: bool = False

    def __init__(
        self,
        settings: BaseSettings = Settings(),
    ):

        self.settings = settings
        self.client: GraphDatabase = GraphDatabase.driver(
            str(self.settings.db_uri),
            auth=("", ""),
        )

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Close the database connection when exiting the context."""
        if self.client:
            self.client.close()
            logger.debug("Database connection closed.")

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type
        return new_cls

    def setup(self) -> bool:

        try:
            if self._is_initialized:
                return True

            self.client.verify_connectivity()
            self._is_initialized = True
            logger.info("Database schema initialized successfully.")

        except Exception as e:
            logger.error(f"Error initializing the database connection: {e}")
            raise StorageError(f"Database connection error: {e}") from e

        return self._is_initialized

    def insert_many(
        self,
        contents: list[T],
    ) -> int:
        """
        Flatten the composable objects to retain only the necessary fields
        and insert them into the database.
        """
        raise NotImplementedError(
            "This method should be overridden by subclasses to implement the insertion logic."
        )

    def select(
        self,
        content_id: str,
    ) -> T:
        raise NotImplementedError(
            "This method should be overridden by subclasses to implement the selection logic."
        )

    @validate_call
    def add_relationship(
        self,
        content: Composable,
        relation_type: RelationshipType,
        related_content: Composable,
    ) -> Relationship:
        """


        assumes that the content exists in the database, or raises an error if it does not.
        """
        if not self._is_initialized:
            self.setup()

        if not self.select(content.uid):
            raise StorageError(
                f"Content with ID '{content.uid}' is missing or invalid."
            )

        # verify the related content is a valid related content
        try:
            ...

        except Exception as e:
            logger.error(
                f"Error adding relationship '{relation_type}' between {relation_type} '{content.uid}' and {relation_type} '{related_content.uid}': {e}"
            )

            raise StorageError(
                f"Invalid related content with ID '{related_content.uid}': {e}"
            ) from e
        finally:
            ...

        return Relationship(
            from_entity=content,
            relation_type=relation_type,
            to_entity=related_content,
        )

    def get_related(
        self, content: Film, relation_type: RelationshipType = None
    ) -> Sequence[Relationship]:
        """
        Retrieve relationships of a specific type for a given content.

        Args:
            content (Film): The content to retrieve relationships for.
            relation_type (RelationshipType, optional): The type of relationship to filter by. Defaults to None,
                in which case all relationships are returned.

        Returns:
            Sequence[Relationship]: A sequence of relationships matching the criteria.
        """
        if not self._is_initialized:
            self.setup()

        return []
