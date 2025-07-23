from typing import Sequence

from loguru import logger
from neo4j import Session

from src.entities.film import Film
from src.entities.woa import WOAType

from .mg_core import AbstractMemGraph


class FilmGraphHandler(AbstractMemGraph[Film]):

    def insert_many(
        self,
        contents: Sequence[Film],
    ) -> int:
        """only interesting film props are retained in the database,
        i.e. title, permalink, uid, directed_by, media, influences, specifications, actors

        NB: when storing in DB, serialization aliases are not used (useless for DB),
        so the field names are the same as in the model definition.
        This makes testing more robust.
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
                    by_alias=False,
                )
                for content in contents
            ]

            # deduplicate rows based on 'uid'
            unique_rows = {row["uid"]: row for row in rows}
            rows = list(unique_rows.values())

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

            logger.error(f"Error inserting films: {e}")
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

        try:

            session: Session = self.client.session()

            with session:

                result = session.run(
                    f"""
                    MATCH (n:Film {{uid: '{content_id}'}})
                    RETURN n
                    LIMIT 1;
                    """
                )

                doc = dict(result.fetch(1)[0].get("n"))

                doc["woa_type"] = WOAType.FILM

                return self.entity_type.model_validate(
                    doc, by_alias=False, by_name=True
                )

        except IndexError as e:
            logger.warning(f"Document with ID '{content_id}' not found: {e}")
            return None

        except Exception as e:

            logger.error(f"Error validating document with ID '{content_id}': {e}")
            return None
