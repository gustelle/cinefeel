from typing import Sequence

from loguru import logger
from neo4j import Session

from src.entities.person import Person

from .mg_core import AbstractMemGraph


class PersonGraphRepository(AbstractMemGraph[Person]):

    def insert_many(
        self,
        contents: Sequence[Person],
    ) -> int:
        """only interesting person props are retained in the database,
        i.e. title, permalink, uid, directed_by, media, influences, specifications, actors

        NB: when storing in DB, serialization aliases are not used (useless for DB),
        so the field names are the same as in the model definition.
        This makes testing more robust.
        """

        try:

            with self.client() as _client:
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

                session: Session = _client.session()

                with session:
                    result = session.run(
                        """
                        UNWIND $rows AS o
                        MERGE (n:Person {uid: o.uid})
                        ON CREATE SET
                                n.title = o.title, 
                                n.permalink = o.permalink,
                                n.media = o.media, 
                                n.biography = o.biography,
                                n.influences = o.influences
                        ON MATCH SET 
                                n.title = o.title, 
                                n.permalink = o.permalink,
                                n.media = o.media, 
                                n.biography = o.biography,
                                n.influences = o.influences
                        RETURN count(n) AS count;
                        """,
                        parameters={"rows": rows},
                    )

                    return result.fetch(1)[0]["count"]

                return 0

        except Exception as e:

            logger.error(f"Error inserting persons: {e}")
            return 0

    def insert(
        self,
        content: Person,
    ) -> int:
        """inserts a single Person entity into the database.

        Args:
            content (Person): The Person entity to be inserted.

        Returns:
            int: The number of nodes inserted (1 if successful, 0 otherwise).
        """

        return self.insert_many([content])

    def update(self, *args, **kwargs):
        raise NotImplementedError("Update method is not implemented yet.")
