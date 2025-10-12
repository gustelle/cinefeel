from datetime import timedelta

from prefect import get_run_logger, task
from prefect.events import emit_event
from prefect.futures import wait
from pydantic import HttpUrl

from src.entities.composable import Composable
from src.entities.movie import Movie
from src.entities.relationship import (
    PeopleRelationshipType,
    Relationship,
    RelationshipType,
)
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.relation_manager import IRelationshipHandler
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.settings import Settings


class EntityRelationshipTask(ITaskExecutor):
    """
    finds relationships between entities.
    and stores them into the graph database.
    """

    settings: Settings
    http_client: IHttpClient

    def __init__(
        self,
        settings: Settings,
        http_client: IHttpClient,
    ):
        self.settings = settings
        self.http_client = http_client

    def _retrieve_page_id(
        self,
        name: str,
    ) -> str | None:
        """
        verifies that a page exists on Wikipedia and retrieves its page ID.

        Returns:
            str | None: the page ID of the page on Wikipedia, or None if not found.
        """

        try:

            logger = get_run_logger()
            if name is None or name.strip() == "":
                logger.warning(f"Invalid name provided: '{name}'")
                return None

            endpoint = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"
            response = self.http_client.send(
                url=endpoint,
                response_type="json",
            )
            return response["key"]
        except KeyError:
            return None
        except HttpError as e:
            if e.status_code == 404:
                logger.warning(f"Page not found for name '{name}'")
                return None
            raise

    def _build_permalink(self, page_id: str) -> HttpUrl:
        """
        builds a permalink from a given page ID.

        Args:
            page_id (str): The page ID to build the permalink from.
        Returns:
            HttpUrl: The constructed permalink.
        """
        return HttpUrl(f"https://fr.wikipedia.org/wiki/{page_id}")

    def load_entity_by_name(
        self, name: str, input_storage: IStorageHandler[Composable]
    ) -> Composable | None:
        """
        retrieves a content from the input storage by its name.

        Args:
            name (str): The name of the entity to extract.
            input_storage (IStorageHandler[Composable]): The storage handler to use for retrieving the entity.

        Returns:
            Composable | None: The extracted entity if successful, None otherwise.


        """
        logger = get_run_logger()

        page_id = self._retrieve_page_id(name=name)

        if page_id is None:
            logger.warning(
                f"Could not find page ID for name '{name}'. Skipping relationship storage."
            )
            return None

        results = input_storage.query(
            permalink=self._build_permalink(page_id=page_id),
            limit=1,
        )

        if results:
            return results[0]

        # send an event to scrape the entity if not found in storage
        logger.info(
            f"Entity with page ID '{page_id}' not found in storage. Triggering extraction flow."
        )
        emit_event(
            event="extract.entity",
            resource={"prefect.resource.id": page_id},
            payload={"entity_type": input_storage.entity_type.__name__},
        )

    @task(
        task_run_name="connect_by_name-{entity.uid}-{name}",
    )
    def connect_by_name(
        self,
        entity: Composable,
        name: str,
        relation: RelationshipType,
        storage: IRelationshipHandler,
    ) -> Relationship | None:
        """Connects an entity to another entity.

        Args:
            entity (Composable): The source entity.
            name (str): The name of the target entity.
            relation (RelationshipType): The type of relationship.
            storage (IRelationshipHandler): The storage handler for relationships.

        Returns:
            Relationship | None: The created relationship or None if unsuccessful.
        """

        related_entity: Composable = self.load_entity_by_name(
            name=name, input_storage=storage
        )

        if related_entity is None:
            return None

        return storage.add_relationship(
            relationship=Relationship(
                from_entity=entity,
                to_entity=related_entity,
                relation_type=relation,
            )
        )

    @task(
        task_run_name="analyze_relationships-{entity.uid}",
    )
    def analyze_relationships(
        self,
        entity: Composable,
        output_storage: IRelationshipHandler,
    ) -> Composable:
        """
        discovers relationships for a given entity and stores them in the graph database.

        Args:
            entity (Composable): The entity to analyze.
            output_storage (IRelationshipHandler): The storage handler to use for storing the relationships.

        """

        logger = get_run_logger()

        _futures = []

        if isinstance(entity, Movie):

            if (
                entity.specifications is not None
                and entity.specifications.directed_by is not None
            ):

                for name in entity.specifications.directed_by:

                    _futures.append(
                        self.connect_by_name.submit(
                            entity=entity,
                            name=name,
                            relation=PeopleRelationshipType.DIRECTED_BY,
                            storage=output_storage,
                        )
                    )

            # retrieve the persons that wrote the script of the film
            if (
                entity.specifications is not None
                and entity.specifications.written_by is not None
            ):

                for name in entity.specifications.written_by:

                    _futures.append(
                        self.connect_by_name.submit(
                            entity=entity,
                            name=name,
                            relation=PeopleRelationshipType.WRITTEN_BY,
                            storage=output_storage,
                        )
                    )

            # retrieve the persons that composed the music of the film
            if (
                entity.specifications is not None
                and entity.specifications.music_by is not None
            ):

                for name in entity.specifications.music_by:

                    _futures.append(
                        self.connect_by_name.submit(
                            entity=entity,
                            name=name,
                            relation=PeopleRelationshipType.COMPOSED_BY,
                            storage=output_storage,
                        )
                    )

            # retrieve the persons that influenced the film
            if entity.influences is not None and len(entity.influences) > 0:
                for influence in entity.influences:
                    if influence.persons is not None and len(influence.persons) > 0:
                        for name in influence.persons:
                            _futures.append(
                                self.connect_by_name.submit(
                                    entity=entity,
                                    name=name,
                                    relation=PeopleRelationshipType.INFLUENCED_BY,
                                    storage=output_storage,
                                )
                            )

            # retrieve the persons that did the special effects of the film
            if (
                entity.specifications is not None
                and entity.specifications.special_effects_by is not None
            ):

                for name in entity.specifications.special_effects_by:

                    _futures.append(
                        self.connect_by_name.submit(
                            entity=entity,
                            name=name,
                            relation=PeopleRelationshipType.SPECIAL_EFFECTS_BY,
                            storage=output_storage,
                        )
                    )

            for future in _futures:
                try:
                    future.result(
                        raise_on_failure=True,
                        timeout=self.settings.prefect_task_timeout,
                    )
                    logger.info(
                        f"Relationship analysis completed for entity '{entity.uid}'."
                    )
                except TimeoutError:
                    logger.warning(f"Task timed out for {future.task_run_id}.")
                except Exception as e:
                    logger.error(f"Error in task execution: {e}")

        return entity

    @task()
    def execute_task(
        self,
        input_storage: IStorageHandler[Composable],
        output_storage: IRelationshipHandler[Composable],
    ) -> None:

        logger = get_run_logger()

        try:

            _futures = []

            for uid, entity in input_storage.scan():

                _futures.append(
                    self.analyze_relationships.with_options(
                        cache_key_fn=lambda *_: f"analyze_relationships-{uid}",
                        cache_expiration=timedelta(hours=1),  # 1 hour
                    ).submit(
                        entity=entity,
                        output_storage=output_storage,
                    )
                )

            wait(_futures)

        except Exception as e:
            logger.error(f"Error executing relationship flow: {e}")

        # Iterate over the batch
        # pass the batch to the graph database
        # and insert it
