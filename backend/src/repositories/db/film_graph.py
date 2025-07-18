import kuzu
from loguru import logger
from pydantic import TypeAdapter

from src.entities.film import Film
from src.interfaces.relation_manager import (
    RelationshipType,
)

from .abstract_graph import AbstractGraphHandler


class FilmGraphHandler(AbstractGraphHandler[Film]):

    def select(
        self,
        content_id: str,
    ) -> Film | None:
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

                doc = docs[0]

                for (
                    root_field_name,
                    root_field_definition,
                ) in Film.model_fields.items():
                    if root_field_name in doc and root_field_name in [
                        "summary",
                        "media",
                        "influences",
                        "specifications",
                        "actors",
                    ]:
                        # load json parts
                        try:
                            doc[root_field_name] = TypeAdapter(
                                root_field_definition.annotation
                            ).validate_json(doc[root_field_name], by_name=True)
                        except Exception as e:
                            logger.warning(
                                f"field '{root_field_name}' will be ignored: {e}"
                            )

                return self.entity_type.model_validate(doc, by_name=True)

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

    def get_relationships(
        self,
        content: Film,
        relation_type: RelationshipType,
    ) -> list[Film]:
        """
        Retrieve relationships of a specific type for a given content.

        Args:
            content (Film): The content to retrieve relationships for.
            relation_type (RelationshipType): The type of relationship to retrieve.

        Returns:
            list[Film]: A list of related Film entities.
        """
        if not self._is_initialized:
            self.setup()

        conn = kuzu.Connection(self.client)
        query = f"""
            MATCH (f:Film {{uid: '{content.uid}'}})-[r:{relation_type}]->(related)
            RETURN related
        """
        result = conn.execute(query)

        related_films = []
        while result.has_next():
            related_doc = result.get_next()[0]
            related_films.append(Film.model_validate(related_doc, by_name=True))

        return related_films
