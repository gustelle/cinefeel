from typing import Sequence

from loguru import logger
from neo4j import Session

from src.entities.movie import Movie

from .mg_core import AbstractMemGraph


class MovieGraphRepository(AbstractMemGraph[Movie]):

    def insert_many(
        self,
        contents: Sequence[Movie],
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
                    MERGE (n:Movie {uid: o.uid})
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

            logger.error(f"Error inserting movies: {e}")
            return 0

    def insert(
        self,
        content: Movie,
    ) -> None:
        """inserts a single Movie entity into the database"""

        self.insert_many(contents=[content])

    def update(self, *args, **kwargs):
        raise NotImplementedError("Update method is not implemented yet.")
