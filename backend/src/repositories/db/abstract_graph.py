import tempfile

import kuzu
from loguru import logger
from pydantic import validate_call
from pydantic_settings import BaseSettings

from src.entities.composable import Composable
from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.relation_manager import (
    IRelationshipHandler,
    PeopleRelationshipType,
    Relationship,
    RelationshipType,
)
from src.interfaces.storage import IStorageHandler, StorageError
from src.settings import Settings


class AbstractGraphHandler[T: Film | Person](
    IStorageHandler[T], IRelationshipHandler[T]
):

    client: kuzu.Database
    settings: Settings
    entity_type: type[T]
    _is_initialized: bool = False

    def __init__(
        self,
        client: kuzu.Database | None = None,
        settings: BaseSettings = Settings(),
    ):
        """if not client is provided, it will use an in-memory instance of kuzu."""

        self.settings = settings

        self.client = client or kuzu.Database(
            database_path=self.settings.db_persistence_directory,  # will fallback to in-memory if not set
            max_db_size=self.settings.db_max_size,
        )

        logger.info(f"Connected to Kuzu database '{self.client.database_path}' ")

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

        conn = kuzu.Connection(self.client)
        conn.execute("INSTALL json;LOAD json;")

        conn.execute(
            """
                CREATE NODE TABLE IF NOT EXISTS Film (
                    uid STRING, 
                    title STRING, 
                    permalink STRING, 
                    summary STRING,
                    media JSON,
                    specifications JSON,
                    actors JSON, 
                    PRIMARY KEY (uid)
                );
            """
        )
        conn.execute(
            """
                CREATE NODE TABLE IF NOT EXISTS Person (
                    uid STRING, 
                    title STRING, 
                    permalink STRING, 
                    biography JSON,
                    media JSON,
                    characteristics JSON,
                    PRIMARY KEY (uid)
                );
            """
        )

        for relation_type in list(PeopleRelationshipType):
            conn.execute(
                f"""
                    CREATE REL TABLE IF NOT EXISTS {relation_type.value} (FROM Film TO Person);
                """
            )

        # later on we can add the company relationships
        # for relation_type in list(CompanyRelationshipType):
        #     conn.execute(
        #         f"""
        #             CREATE REL TABLE IF NOT EXISTS {relation_type.value} (FROM Film TO Company);
        #         """
        #     )

        logger.info("Database schema initialized successfully.")

        conn.close()

        self._is_initialized = True
        return self._is_initialized

    def insert_many(
        self,
        contents: list[T],
    ) -> int:
        """
        TODO:
        - test this method in particular the RuntimeError: Copy exception: Found duplicated primary key value georgesmelies, which violates the uniqueness constraint of the primary key column
        """

        try:

            if not self._is_initialized:
                self.setup()

            conn = kuzu.Connection(self.client)

            # deduplicate documents by their UID
            contents = {doc.uid: doc for doc in contents}.values()

            # create a temp json file to dump the documents
            # and load from JSON
            with tempfile.NamedTemporaryFile() as temp:
                # dump the documents to a JSON file
                temp.write(
                    b"["
                    + b",".join(
                        [doc.model_dump_json().encode("utf-8") for doc in contents]
                    )
                    + b"]"
                )
                temp.flush()

                entity_type = self.entity_type.__name__

                conn.execute(
                    f"""
                    COPY {entity_type} FROM '{temp.name}' (file_format = 'json');
                    """
                )
                logger.info(f"Documents of type '{entity_type}' created successfully.")
                return len(contents)

            return 0

        except Exception as e:
            logger.error(f"Error inserting documents: {e}")
            return 0

    def select(
        self,
        content_id: str,
    ) -> T:
        """
        Retrieve a document by its ID.

        Returns:
            T: The document with the specified ID.
        """
        conn = kuzu.Connection(self.client)

        entity_type = self.entity_type.__name__

        try:

            result = conn.execute(
                f"""
                MATCH (n:{entity_type} {{uid: '{content_id}'}})
                RETURN n LIMIT 1
                """
            )
            if result.has_next():

                docs = result.get_next()

                if not docs:
                    logger.warning(f"No document found with ID '{content_id}'.")
                    return None

                return self.entity_type.model_validate(docs[0])

            else:
                logger.warning(
                    f"Document with ID '{content_id}' not found in the database."
                )
                return None

        except Exception as e:
            logger.error(f"Error validating document with ID '{content_id}': {e}")
            return None
        finally:
            conn.close()

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
                f"Content with ID '{content.uid}' does not exist in the database."
            )

        # verify the related content is a valid related content
        try:
            conn = kuzu.Connection(self.client)
            content_type = self.entity_type.__name__
            related_type = related_content.__class__.__name__
            result = conn.execute(
                f"""
                MATCH (n:{related_type} {{uid: '{related_content.uid}'}})
                RETURN n LIMIT 1
                """
            )
            if result.has_next():

                # add relationships if any
                conn.execute(
                    f"""
                    MATCH (f:{content_type} {{uid: '{content.uid}'}}), (p:{related_type} {{uid: '{related_content.uid}'}})
                    CREATE (f)-[:{relation_type.value}]->(p);
                    """
                )
                logger.info(
                    f"Relationship '{relation_type.value}' between {content_type} '{content.uid}' and {related_type} '{related_content.uid}' created successfully."
                )

            else:
                raise StorageError(
                    f"Related content with ID '{related_content.uid}' does not exist in the database."
                )
        except Exception as e:
            logger.error(
                f"Error adding relationship '{relation_type}' between {content_type} '{content.uid}' and {related_type} '{related_content.uid}': {e}"
            )

            raise StorageError(
                f"Invalid related content with ID '{related_content.uid}': {e}"
            ) from e
        finally:
            conn.close()

        return Relationship(
            from_entity=content,
            relation_type=relation_type,
            to_entity=related_content,
        )
