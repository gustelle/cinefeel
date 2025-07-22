import kuzu
from loguru import logger
from pydantic import TypeAdapter

from src.entities.person import Person

from .mg_core import AbstractMemGraph


class PersonGraphHandler(AbstractMemGraph[Person]):

    def select(
        self,
        content_id: str,
    ) -> Person | None:
        """
        Retrieve a document by its ID.

        Returns:
            T: The document with the specified ID.
        """
        return None
        conn = kuzu.Connection(self.client)

        logger.debug(f"select person Using client: {self.client.database_path}")

        entity_type = self.entity_type.__name__

        try:

            result = conn.execute(
                f"""
                MATCH (n:{entity_type} {{uid: '{content_id}'}})
                RETURN n LIMIT 1;
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
                ) in Person.model_fields.items():
                    if root_field_name in doc and root_field_name in [
                        "biography",
                        "media",
                        "characteristics",
                        "influences",
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
