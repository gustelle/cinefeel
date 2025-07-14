import kuzu
from loguru import logger
from pydantic_settings import BaseSettings

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.relation_manager import Relationship
from src.interfaces.storage import StorageError
from src.settings import Settings

from .abstract_graph import AbstractGraphHandler


class FimGraphHandler(AbstractGraphHandler[Film]):

    # required to handle relationships with Person entities
    person_client: AbstractGraphHandler[Person]

    def __init__(
        self,
        client: kuzu.Database | None = None,
        settings: BaseSettings = Settings(),
    ):
        super().__init__(client, settings)
        self.person_client = AbstractGraphHandler[Person](client, settings)

    def add_relationship(
        self, content: Film, relation_name: str, related_content: Person
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

        # verify the person is a valid related content
        try:
            conn = kuzu.Connection(self.client)
            result = conn.execute(
                f"""
                MATCH (n:Person {{uid: '{related_content.uid}'}})
                RETURN n LIMIT 1
                """
            )
            if result.has_next():

                # add relationships if any
                if relation_name == "directed_by":
                    conn.execute(
                        f"""
                        MATCH (f:Film {{uid: '{content.uid}'}}), (p:Person {{uid: '{related_content.uid}'}})
                        CREATE (f)-[:DirectedBy]->(p);
                        """
                    )
                    logger.info(
                        f"Relationship 'DirectedBy' between Film '{content.uid}' and Person '{related_content.uid}' created successfully."
                    )

            else:
                raise StorageError(
                    f"Related content with ID '{related_content.uid}' does not exist in the database."
                )
        except Exception as e:
            logger.error(
                f"Error adding relationship '{relation_name}' between Film '{content.uid}' and Person '{related_content.uid}': {e}"
            )

            raise StorageError(
                f"Invalid related content with ID '{related_content.uid}': {e}"
            ) from e
        finally:
            conn.close()

        return Relationship(
            from_entity=content,
            relation_type=relation_name,
            to_entity=related_content,
        )
