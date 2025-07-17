import kuzu
from loguru import logger
from pydantic_settings import BaseSettings

from src.entities.film import Film
from src.entities.person import Biography, Person
from src.settings import Settings

from .abstract_graph import AbstractGraphHandler


class PersonGraphHandler(AbstractGraphHandler[Person]):

    # required to handle relationships with Film entities
    film_client: AbstractGraphHandler[Film]

    def __init__(
        self,
        client: kuzu.Database | None = None,
        settings: BaseSettings = Settings(),
    ):
        super().__init__(client, settings)
        self.film_client = AbstractGraphHandler[Film](client, settings)

    def select(
        self,
        content_id: str,
    ) -> Person | None:
        """
        Retrieve a document by its ID.

        TODO:
        - the object is stored as JSON, so we need to parse it
        - example: biography = Biography.model_validate(docs[0]["biography"], by_name=True)
        - test model_validate(docs[0], by_name=True)

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

                if "biography" in doc:
                    # if the document has a biography, we need to validate it
                    try:
                        doc["biography"] = Biography.model_validate_json(
                            doc["biography"], by_name=True
                        )
                    except Exception as e:
                        logger.error(
                            f"Error validating biography for document with ID '{content_id}': {e}"
                        )
                        return None

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
