from typing import Sequence

from loguru import logger
from neo4j import Session

from src.entities.film import Film

from .mg_core import AbstractMemGraph


class FilmGraphHandler(AbstractMemGraph[Film]):

    def insert_many(
        self,
        contents: Sequence[Film],
    ) -> int:
        """only interesting film props are retained in the database,
        i.e. title, permalink, uid, directed_by, media, influences, specifications, actors
        """

        try:

            if not self._is_initialized:
                self.setup()

                # Convert contents to a Polars DataFrame
                rows = [
                    content.model_dump(
                        exclude_unset=True,
                        exclude_none=True,
                        mode="json",
                    )
                    for content in contents
                ]

                logger.debug(rows)

                session: Session = self.client.session()

                with session:
                    result = session.run(
                        """
                        UNWIND $rows AS o
                        MERGE (n:Film {uid: o.uid})
                        ON CREATE SET   
                                n.title = o.title, n.permalink = o.permalink,
                                n.media = o.media, n.influences = o.influences,
                                n.specifications = o.specifications, n.actors = o.actors
                        ON MATCH SET 
                                n.title = o.title, n.permalink = o.permalink,
                                n.media = o.media, n.influences = o.influences,
                                n.specifications = o.specifications, n.actors = o.actors
                        RETURN count(n) AS count;
                        """,
                        parameters={"rows": rows},
                    )

                    return result.fetch(1)[0]["count"]

            return 0

        except Exception as e:

            logger.error(f"Error inserting documents: {e}")
            return 0

    def select(
        self,
        content_id: str,
    ) -> Film | None:
        """
        Retrieve a document by its ID.

        Returns:
            T: The document with the specified ID.
        """
        return None
        # conn = kuzu.Connection(self.client)

        # entity_type = self.entity_type.__name__

        # try:

        #     result = conn.execute(
        #         f"""
        #         MATCH (n:{entity_type} {{uid: '{content_id}'}})
        #         RETURN n
        #         LIMIT 1;
        #         """
        #     )

        #     for doc in result:

        #         doc = doc[0]  # Get the first element of the result

        #         for (
        #             root_field_name,
        #             root_field_definition,
        #         ) in Film.model_fields.items():
        #             if root_field_name in doc and root_field_name in [
        #                 "summary",
        #                 "media",
        #                 "influences",
        #                 "specifications",
        #                 "actors",
        #             ]:
        #                 # load json parts
        #                 try:
        #                     doc[root_field_name] = TypeAdapter(
        #                         root_field_definition.annotation
        #                     ).validate_json(doc[root_field_name], by_name=True)
        #                 except Exception as e:
        #                     logger.warning(
        #                         f"field '{root_field_name}' will be ignored: {e}"
        #                     )

        #         return self.entity_type.model_validate(doc, by_name=True)

        #     else:
        #         logger.warning(
        #             f"Document with ID '{content_id}' is missing or invalid."
        #         )
        #         return None

        # except Exception as e:
        #     import traceback

        #     logger.error(traceback.format_exc())
        #     logger.error(f"Error validating document with ID '{content_id}': {e}")
        #     return None
        # finally:
        #     conn.close()
