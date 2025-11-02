import importlib
from contextlib import contextmanager
from typing import Generator, Sequence

from loguru import logger
from neo4j import GraphDatabase, Session
from pydantic import ValidationError

from src.entities.composable import Composable
from src.entities.relationship import (
    BaseRelationship,
    LooseRelationship,
    RelationshipType,
    StrongRelationship,
)
from src.exceptions import RelationshipError, StorageError
from src.interfaces.storage import IRelationshipHandler
from src.settings import StorageSettings


class AbstractMemGraph[T: Composable](IRelationshipHandler[T]):
    """
    Base class for MemoryGraph DB storage handler.

    **This class SHOULD NOT be instantiated directly, but rather extended by specific entity repositories.
    e.g. MovieGraphRepository, PersonGraphRepository, etc.**
    """

    settings: StorageSettings
    entity_type: type[T]

    def __init__(
        self,
        settings: StorageSettings | None = None,
    ):
        self.settings = settings or StorageSettings()

    @contextmanager
    def client(self):
        _client = GraphDatabase.driver(
            str(self.settings.graphdb_uri),
            auth=("", ""),
        )
        try:
            _client.verify_connectivity()
            yield _client
        finally:
            _client.close()

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type
        return new_cls

    def on_init(self):

        with self.client() as _client:
            try:

                # create indexes if they do not exist
                session: Session = _client.session()
                with session:
                    session.run(
                        f"""
                            CREATE INDEX ON :{self.entity_type.__name__}(uid);
                            CREATE INDEX ON :{self.entity_type.__name__}(permalink);
                            """
                    )
                    logger.info(
                        f"Indexes for '{self.entity_type.__name__}' ensured in MemoryGraphDB."
                    )

            except Exception:
                logger.warning(
                    f"Index for {self.entity_type.__name__} already exists or could not be created."
                )

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
        Retrieve a `Composable` by its unique identifier.

        Args:
            content_id (str): The unique identifier of the `Composable`.

        Returns:
            T: The `Composable` with the specified ID.
        """
        try:

            with self.client() as _client:

                session: Session = _client.session()

                with session:

                    result = session.run(
                        f"""
                        MATCH (n:{self.entity_type.__name__} {{uid: '{content_id}'}})
                        RETURN n
                        LIMIT 1;
                        """
                    )

                    doc = dict(result.fetch(1)[0].get("n"))

                    return self.entity_type.model_validate(doc, by_name=True)

        except IndexError as e:
            logger.warning(f"Document with ID '{content_id}' not found: {e}")
            return None

        except Exception as e:

            logger.error(f"Error validating document with ID '{content_id}': {e}")
            return None

    def add_relationship(
        self,
        relationship: BaseRelationship,
    ) -> None:
        """
        adds a relationship between two contents in the database,

        Args:
            relationship (BaseRelationship): The relationship to add.
                the relationship can be strong or loose

        Raises:
            RelationshipError
        """

        try:
            with self.client() as _client:
                session: Session = _client.session()

                with session:

                    if relationship.is_strong:

                        session.run(
                            f"""
                            MATCH (c1:{relationship.from_entity_type} {{uid: $from_uid}}), (c2:{relationship.to_entity_type} {{uid: $to_uid}})
                            MERGE (c1)-[r:{relationship.relation_type.value} {{is_strong: true}}]->(c2)
                            RETURN r, c1, c2;
                            """,
                            parameters={
                                "from_uid": relationship.from_entity.uid,
                                "to_uid": relationship.to_entity.uid,
                            },
                        )

                        logger.info(
                            f"Stored strong relationship '{relationship.from_entity.uid}' -[{relationship.relation_type}]-> '{relationship.to_entity.uid}'."
                        )

                    else:

                        session.run(
                            f"""
                            MERGE (c2:{relationship.to_entity_type} {{title: $to_title}})
                            """,
                            parameters={"to_title": relationship.to_title},
                        )

                        _ = session.run(
                            f"""
                            MATCH (c1:{relationship.from_entity_type} {{uid: $from_uid}}), (c2:{relationship.to_entity_type} {{title: $to_title}})
                            MERGE (c1)-[r:{relationship.relation_type.value} {{is_strong: false}}]->(c2)
                            RETURN r, c1, c2;
                            """,
                            parameters={
                                "from_uid": relationship.from_entity.uid,
                                "to_title": relationship.to_title,
                            },
                        )

                        logger.info(
                            f"Stored loose relationship '{relationship.from_entity.uid}' -[{relationship.relation_type}]-> '{relationship.to_title}'."
                        )

        except Exception as e:
            raise RelationshipError(
                f"Invalid relationship {relationship.model_dump()}: {e}"
            ) from e

    def get_related(
        self, content: T, relation_type: RelationshipType = None
    ) -> Sequence[BaseRelationship]:
        """
        Retrieve relationships for a given content,
            both strong and loose relationships are returned.
            when relation_type is specified, only relationships of that type are returned.

        Args:
            content (T): The content to retrieve relationships for.
            relation_type (RelationshipType, optional): The type of relationship to filter by. Defaults to None,
                in which case all relationships are returned.

        Returns:
            Sequence[BaseRelationship]: A sequence of relationships matching the criteria; either strong or loose.
                empty if none found.
        """

        try:
            with self.client() as _client:
                session: Session = _client.session()

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
                            # this is a loose relationship
                            rels.append(
                                LooseRelationship(
                                    from_entity=content,
                                    to_title=result.get("n").get("title"),
                                    relation_type=RelationshipType.from_string(
                                        result.get("r").type
                                    ),
                                )
                            )
                        else:
                            # this is a strong relationship
                            rels.append(
                                StrongRelationship(
                                    from_entity=content,
                                    to_entity=related_type.model_validate(
                                        dict(result.get("n")),
                                        by_alias=False,
                                        by_name=True,
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

    def scan(self) -> Generator[tuple[str, T], None, None]:

        try:

            with self.client() as _client:

                _last_uid = ""

                while _last_uid is not None:

                    try:

                        session: Session = _client.session()

                        with session:

                            result = session.run(
                                f"""
                                MATCH (n:{self.entity_type.__name__})
                                WHERE n.uid IS NOT NULL AND n.uid > $uid
                                RETURN n
                                ORDER BY n.uid ASC
                                LIMIT 1;
                                """,
                                parameters={"uid": _last_uid},
                            )

                            if not result.peek():
                                # stop if no more results
                                logger.debug(
                                    f"No more '{self.entity_type.__name__}' found after UID '{_last_uid}'"
                                )
                                break

                            doc = dict(result.fetch(1)[0].get("n"))

                            _last_uid = doc.get("uid")

                            yield _last_uid, self.entity_type.model_validate(
                                doc, by_name=True
                            )

                    except (IndexError, KeyError, ValidationError):
                        logger.warning(
                            f"No documents found for entity type '{self.entity_type.__name__}'"
                        )
                        continue

        except Exception as e:

            logger.error(f"Error scanning for documents: {e}")
            return None

    def query(
        self,
        order_by: str = "uid",
        permalink: str | None = None,
        after: T | None = None,
        limit: int = 100,
    ) -> Sequence[T]:

        try:

            with self.client() as _client:

                q = f"""
                    MATCH (n:{self.entity_type.__name__})
                    WHERE 
                    {'n.uid > $after_uid' if after else '1=1'}
                    AND 
                    {'n.permalink = $permalink' if permalink else '1=1'}
                    RETURN n
                    ORDER BY n.{order_by} ASC
                    LIMIT $limit;
                """
                session: Session = _client.session()

                with session:

                    results = session.run(
                        q,
                        parameters={
                            "order_by": order_by,
                            "permalink": str(permalink) if permalink else "",
                            "after_uid": after.uid if after else "",
                            "limit": limit,
                        },
                    )

                    if not results.peek():
                        logger.warning(
                            f"No '{self.entity_type.__name__}' found matching the criteria"
                        )
                        return []

                    return [
                        self.entity_type.model_validate(
                            dict(result.get("n")), by_name=True
                        )
                        for result in results
                    ]

        except Exception as e:

            msg = f"""
            Error executing query for '{self.entity_type.__name__}': {e}
            Query: {q}
            Parameters: {{
                "order_by": {order_by},
                "permalink": {permalink},
                "after_uid": {after.uid if after else ""},
                "limit": {limit}
            }}
            """

            raise StorageError(msg) from e
