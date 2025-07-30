from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import PrefectFuture
from pydantic import HttpUrl

from src.entities.composable import Composable
from src.entities.film import Film
from src.entities.relationship import PeopleRelationshipType, Relationship
from src.interfaces.http_client import IHttpClient
from src.interfaces.relation_manager import IRelationshipHandler
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.db.person_graph import PersonGraphHandler
from src.settings import Settings


class RelationshipFlow(ITaskExecutor):
    """
    flow in charge of finding relationships between entities.
    and storing them into the graph database.

    This flow starts from json files stored in the local storage.
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

    def get_permalink_by_name(
        self,
        name: str,
    ) -> HttpUrl | None:
        """
        Returns:
            HttpUrl | None: the permalink of the person on Wikipedia, or None if not found.
        """

        try:
            endpoint = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"
            response = self.http_client.send(
                url=endpoint,
                response_type="json",
            )
            page_id = response["key"]
            return HttpUrl(f"https://fr.wikipedia.org/wiki/{page_id}")
        except KeyError:
            return None

    @task(
        cache_policy=NO_CACHE,
    )
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

        Raises:
            ValueError: If no entity is found for the given name in the storage,
                in which case the failure should be catched by the caller
                to extract the entity from the web.
        """
        logger = get_run_logger()

        permalink = self.get_permalink_by_name(name=name)

        if permalink is None:
            logger.warning(
                f"Could not find permalink for name '{name}'. Skipping relationship storage."
            )
            return None

        results = input_storage.query(
            permalink=permalink,
            limit=1,
        )

        if results:
            return results[0]

        raise ValueError(f"No entity found for name '{name}' in storage.")

    @task(
        task_run_name="do_enrichment-{relationship.from_entity.uid}-{relationship.to_entity.uid}",
        cache_policy=NO_CACHE,
        retries=3,
        retry_delay_seconds=[2, 5, 10],
    )
    def do_enrichment(
        self,
        relationship: Relationship,
        output_storage: IRelationshipHandler,
    ) -> Relationship:
        """
        Operates the storage of a relationship between two entities in the graph database.

        Args:
            relationship (Relationship): The relationship to store.
            output_storage (IRelationshipHandler): The handler to use for storing the relationship.

        """

        result = output_storage.add_relationship(relationship=relationship)

        return result

    @task(task_run_name="analyze_relationships-{entity.uid}", cache_policy=NO_CACHE)
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

        if isinstance(entity, Film):

            if (
                entity.specifications is not None
                and entity.specifications.directed_by is not None
            ):

                for name in entity.specifications.directed_by:

                    related_entity: Composable = self.load_entity_by_name(
                        name=name,
                        input_storage=PersonGraphHandler(
                            settings=self.settings,
                        ),
                    )

                    if related_entity is None:
                        continue

                    _fut_relationship: PrefectFuture = self.do_enrichment.submit(
                        relationship=Relationship(
                            from_entity=entity,
                            to_entity=related_entity,
                            relation_type=PeopleRelationshipType.DIRECTED_BY,
                        ),
                        output_storage=output_storage,
                    )

                    _futures.append(_fut_relationship)

            # retrieve the persons that wrote the script of the film
            if (
                entity.specifications is not None
                and entity.specifications.written_by is not None
            ):

                for name in entity.specifications.written_by:

                    related_entity: Composable = self.load_entity_by_name(
                        name=name,
                        input_storage=PersonGraphHandler(
                            settings=self.settings,
                        ),
                    )

                    if related_entity is None:
                        continue

                    _fut_relationship: PrefectFuture = self.do_enrichment.submit(
                        relationship=Relationship(
                            from_entity=entity,
                            to_entity=related_entity,
                            relation_type=PeopleRelationshipType.WRITTEN_BY,
                        ),
                        output_storage=output_storage,
                    )

                    _futures.append(_fut_relationship)

            # retrieve the persons that composed the music of the film
            if (
                entity.specifications is not None
                and entity.specifications.music_by is not None
            ):

                for name in entity.specifications.music_by:

                    related_entity: Composable = self.load_entity_by_name(
                        name=name,
                        input_storage=PersonGraphHandler(
                            settings=self.settings,
                        ),
                    )

                    if related_entity is None:
                        continue

                    _fut_relationship: PrefectFuture = self.do_enrichment.submit(
                        relationship=Relationship(
                            from_entity=entity,
                            to_entity=related_entity,
                            relation_type=PeopleRelationshipType.COMPOSED_BY,
                        ),
                        output_storage=output_storage,
                    )

                    _futures.append(_fut_relationship)

            # retrieve the persons that influenced the film
            if entity.influences is not None and len(entity.influences) > 0:

                for influence in entity.influences:
                    if influence.persons is not None and len(influence.persons) > 0:
                        for name in influence.persons:

                            related_entity: Composable = self.load_entity_by_name(
                                name=name,
                                input_storage=PersonGraphHandler(
                                    settings=self.settings,
                                ),
                            )

                            if related_entity is None:
                                continue

                            _fut_relationship: PrefectFuture = (
                                self.do_enrichment.submit(
                                    relationship=Relationship(
                                        from_entity=entity,
                                        to_entity=related_entity,
                                        relation_type=PeopleRelationshipType.INFLUENCED_BY,
                                    ),
                                    output_storage=output_storage,
                                )
                            )

                            _futures.append(_fut_relationship)

            # retrieve the company that produced the film
            ...
            # retrieve the company that distributed the film
            ...
            # retrieve the persons that did the special effects of the film
            ...
            # retrieve the persons that did the scenography of the film
            ...
            # retrieve the persons that influenced the film
            ...
            # retrieve actors that played in the film
            ...

            for future in _futures:
                try:
                    future.result(
                        raise_on_failure=True,
                        timeout=self.settings.task_timeout,
                    )
                    logger.info(
                        f"Relationship analysis completed for entity '{entity.uid}'."
                    )
                except TimeoutError:
                    logger.warning(f"Task timed out for {future.task_run_id}.")
                except Exception as e:
                    logger.error(f"Error in task execution: {e}")

        return entity

    def execute(
        self,
        input_storage: IStorageHandler[Composable],
        output_storage: IRelationshipHandler[Composable],
    ) -> None:

        logger = get_run_logger()

        try:

            # send concurrent tasks to analyze HTML content
            # don't wait for the task to be completed
            storage_futures = []

            # need to keep track of the futures to wait for them later
            # see: https://github.com/PrefectHQ/prefect/issues/17517
            entity_futures = []

            for entity in input_storage.scan():

                logger.info(
                    f"Found entity '{entity.uid}' in json storage, launching analysis."
                )

                future_entity = self.analyze_relationships.submit(
                    entity=entity,
                    output_storage=output_storage,
                )
                entity_futures.append(future_entity)

            # now wait for all tasks to complete
            future_storage: PrefectFuture
            for future_storage in storage_futures + entity_futures:
                try:
                    future_storage.result(
                        raise_on_failure=True, timeout=self.settings.task_timeout
                    )
                except TimeoutError:
                    logger.warning(f"Task timed out for {future_storage.task_run_id}.")
                except Exception as e:
                    logger.error(f"Error in task execution: {e}")

        except Exception as e:
            logger.error(f"Error executing relationship flow: {e}")

        # Iterate over the batch
        # pass the batch to the graph database
        # and insert it
