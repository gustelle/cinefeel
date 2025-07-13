import tempfile
from typing import Generator

import kuzu
from loguru import logger

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class GraphDBStorage[T: Film | Person](IStorageHandler[T]):

    client: kuzu.Database
    settings: Settings
    entity_type: type[Film | Person]
    _is_initialized: bool = False

    def __init__(
        self,
        settings: Settings,
    ):

        self.settings = settings
        self.client = kuzu.Database(settings.db_persistence_directory)

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
        conn.execute(
            """
                CREATE REL TABLE IF NOT EXISTS DirectedBy (FROM Film TO Person);
            """
        )

        conn.close()

        logger.info("KuzuDB client initialized successfully.")
        self._is_initialized = True
        return self._is_initialized

    def insert_many(
        self,
        contents: list[T],
    ) -> int:
        """
        Index a document in the index in upsert mode.
        This means that if the document already exists, it will be updated.
        If it does not exist, it will be created.

        """

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
                + b",".join([doc.model_dump_json().encode("utf-8") for doc in contents])
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

    def scan(self, *args, **kwargs) -> Generator[T, None, None]:
        """Scans the persistent storage and returns a list of all contents."""
        raise NotImplementedError("This method should be overridden by subclasses.")
