import importlib
from typing import Sequence

from loguru import logger
from neo4j import GraphDatabase, Session
from pydantic import validate_call
from pydantic_settings import BaseSettings

from src.entities.composable import Composable
from src.entities.relationship import Relationship, RelationshipType
from src.interfaces.relation_manager import IRelationshipHandler, RelationshipError
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
    ) -> T | None:
        """
        Retrieve a document by its ID.

        Returns:
            T: The document with the specified ID.
        """
        try:

            session: Session = self.client.session()

            with session:

                result = session.run(
                    f"""
                    MATCH (n:{self.entity_type.__name__} {{uid: '{content_id}'}})
                    RETURN n
                    LIMIT 1;
                    """
                )

                doc = dict(result.fetch(1)[0].get("n"))

                return self.entity_type.model_validate(
                    doc, by_alias=False, by_name=True
                )

        except IndexError as e:
            logger.warning(f"Document with ID '{content_id}' not found: {e}")
            return None

        except Exception as e:

            logger.error(f"Error validating document with ID '{content_id}': {e}")
            return None

    @validate_call
    def add_relationship(
        self,
        relationship: Relationship,
    ) -> None:
        """
        assumes that the content exists in the database, or raises an error if it does not.

        Args:
            relationship (Relationship): The relationship to add.
        Raises:
            RelationshipError
        """
        if not self._is_initialized:
            self.setup()

        if not self.select(relationship.from_entity.uid):
            raise RelationshipError(
                f"Content with ID '{relationship.from_entity.uid}' is missing or invalid."
            )

        try:
            session: Session = self.client.session()

            with session:

                session.run(
                    f"""
                    MATCH (c1:{relationship.from_entity.__class__.__name__} {{uid: $from_uid}}), (c2:{relationship.to_entity.__class__.__name__} {{uid: $to_uid}})
                    MERGE (c1)-[r:{relationship.relation_type.value}]->(c2)
                    RETURN r, c1, c2;
                    """,
                    parameters={
                        "from_uid": relationship.from_entity.uid,
                        "to_uid": relationship.to_entity.uid,
                    },
                )

        except Exception as e:
            logger.error(
                f"Error adding relationship '{relationship.relation_type}' between '{relationship.from_entity.uid}' and '{relationship.to_entity.uid}': {e}"
            )
            raise RelationshipError(
                f"Invalid related content with ID '{relationship.to_entity.uid}': {e}"
            ) from e

    def get_related(
        self, content: T, relation_type: RelationshipType = None
    ) -> Sequence[Relationship]:
        """
        Retrieve relationships of a specific type for a given content.

        Args:
            content (T): The content to retrieve relationships for.
            relation_type (RelationshipType, optional): The type of relationship to filter by. Defaults to None,
                in which case all relationships are returned.

        Returns:
            Sequence[Relationship]: A sequence of relationships matching the criteria.
        """
        if not self._is_initialized:
            self.setup()

        try:
            session: Session = self.client.session()

            with session:

                results = session.run(
                    f"""
                    MATCH (:{self.entity_type.__name__} {{uid: $uid}})-[r{':' + relation_type.value if relation_type else ''}]->(n)
                    RETURN labels(n) as labels, n, r;
                    """,
                    parameters={
                        "uid": content.uid,
                    },
                )

                rels = []

                for result in results:
                    first_label = (
                        result.get("labels")[0] if result.get("labels") else None
                    )
                    if first_label is None:
                        continue

                    m = importlib.import_module("src.entities")
                    related_type = getattr(m, first_label, None)
                    if related_type is None:
                        logger.warning(
                            f"Related type '{first_label}' not found in entities module for content with ID '{content.uid}'"
                        )
                        continue

                    rels.append(
                        Relationship(
                            from_entity=content,
                            to_entity=related_type.model_validate(
                                dict(result.get("n")), by_alias=False, by_name=True
                            ),
                            relation_type=RelationshipType.from_string(
                                result.get("r").type
                            ),
                        )
                    )

                return rels

        except Exception as e:
            raise RelationshipError(
                f"Invalid related content with ID '{content.uid}': {e}"
            ) from e

        return []
