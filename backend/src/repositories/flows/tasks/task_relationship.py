from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import PrefectFuture
from pydantic import BaseModel, HttpUrl

from src.entities.composable import Composable
from src.entities.film import Film
from src.entities.person import Person
from src.entities.relationship import (
    CompanyRelationshipType,
    PeopleRelationshipType,
    Relationship,
    RelationshipType,
)
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.db.film_graph import FilmGraphHandler
from src.repositories.db.person_graph import PersonGraphHandler
from src.repositories.local_storage.html_storage import LocalTextStorage
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings

from .task_html_parsing import HtmlParsingFlow


class RelationshipData(BaseModel):
    """
    Data structure for relationship information.
    """

    related_entity_name: str
    relation_type: RelationshipType

    def is_person_relationship(self) -> bool:
        """
        Check if the relationship is a person relationship.

        Returns:
            bool: True if the relationship is a person relationship, False otherwise.
        """
        return isinstance(self.relation_type, PeopleRelationshipType)

    def is_company_relationship(self) -> bool:
        """
        Check if the relationship is a company relationship.

        Returns:
            bool: True if the relationship is a company relationship, False otherwise.
        """
        return isinstance(self.relation_type, CompanyRelationshipType)


class RelationshipFlow(ITaskExecutor):
    """
    flow in charge of finding relationships between entities.
    and storing them into the graph database.

    This flow starts from json files stored in the local storage.
    """

    entity_type: type[Composable]
    settings: Settings
    http_client: IHttpClient

    def __init__(
        self,
        settings: Settings,
        entity_type: type[Composable],
        http_client: IHttpClient,
    ):
        self.settings = settings
        self.entity_type = entity_type
        self.http_client = http_client

    @task(
        task_run_name="download_page-{page_id}",
        retries=3,
        retry_delay_seconds=[1, 2, 5],
        cache_policy=NO_CACHE,
    )
    def download_page(
        self,
        page_id: str,
        output_storage: IStorageHandler | None = None,
        **params,
    ) -> str | None:
        """


        Args:
            page_id (str): The page ID to download.
            output_storage (HtmlContentStorageHandler | None, optional): The storage handler to use for storing the content. Defaults to None.
            **params: Additional parameters for the HTTP request.

        Returns:
            str | None: The content ID if the download was successful, None otherwise.
        """

        logger = get_run_logger()

        # 1. check if the page_id is already stored in the storage_handler
        # in which case we return the page_id
        if output_storage is not None and output_storage.select(content_id=page_id):
            return page_id

        endpoint = f"{self.settings.mediawiki_base_url}/page/{page_id}/html"

        try:

            logger = get_run_logger()

            html = self.http_client.send(
                url=endpoint,
                response_type="text",
                params=params,
            )

            if html is not None and output_storage is not None:
                output_storage.insert(
                    content_id=page_id,
                    content=html,
                )

            return page_id if html is not None else None

        except Exception as e:
            if isinstance(e, HttpError) and e.status_code == 404:
                logger.warning(f"Page {page_id} not found (404).")
                return None
            elif not isinstance(e, HttpError):
                logger.error(f"Error downloading page {page_id}: {e}")
                return None
            else:
                raise

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

    @task(cache_policy=NO_CACHE)
    def get_entity(
        self,
        permalink: HttpUrl,
        entity_type: type[Composable],
    ) -> Composable | None:
        """
        Extracts an entity from the HTML content and stores it using the provided storage handler.

        TODO:
        - test this method

        Args:
            permalink (HttpUrl): The permalink of the entity to extract.
            entity_type (type[Composable]): The type of the entity to extract.

        Returns:
            Composable | None: The extracted entity if successful, None otherwise.
        """
        logger = get_run_logger()

        try:

            tmp_storage = LocalTextStorage(
                path=self.settings.persistence_directory,
                entity_type=entity_type,
            )

            # here we are dealing with a Movie
            json_storage = JSONEntityStorageHandler[entity_type](settings=self.settings)
            results = json_storage.query(
                permalink=permalink,
                limit=1,
            )

            if results:
                return results[0]

            content_id = str(permalink).split("/")[-1]

            html_fut: PrefectFuture = self.download_page.submit(
                page_id=content_id,
                output_storage=tmp_storage,
            )

            html_fut.result(
                raise_on_failure=True,
                timeout=self.settings.task_timeout,
            )

            # trigger the HTML parsing flow
            flow = HtmlParsingFlow(
                settings=self.settings,
                entity_type=entity_type,
            )

            flow.execute(
                content_ids=[content_id],
                input_storage=tmp_storage,
                output_storage=json_storage,
            )

            logger.info(f"HTML parsing flow executed for content ID '{content_id}'.")

            results = json_storage.query(
                permalink=permalink,
                limit=1,
            )

            if results:
                logger.info(f"Entity '{content_id}' extracted successfully.")
                return results[0]

            return None

        except Exception as e:

            logger.error(f"Error extracting entity from HTML: {e}")
            return None

    @task(
        task_run_name="store_relationship",
        cache_policy=NO_CACHE,
        retries=3,
        retry_delay_seconds=[2, 5, 10],
    )
    def do_enrichment(
        self,
        entity: Composable,
        relationship: RelationshipData,
    ) -> Relationship:
        """
        TODO:
        - test this method

        Operates the storage of a relationship between two entities in the graph database.
        """
        logger = get_run_logger()

        permalink = self.get_permalink_by_name(name=relationship.related_entity_name)

        is_person_relation = relationship.is_person_relationship()

        if permalink is None:
            logger.warning(
                f"Could not find permalink for name '{relationship.related_entity_name}'. Skipping relationship storage."
            )
            return None

        related_entity: Composable = self.get_entity(
            permalink=permalink, entity_type=Person if is_person_relation else Film
        )

        if related_entity is not None:

            related_entity_handler = (
                PersonGraphHandler(self.settings)
                if is_person_relation
                else FilmGraphHandler(self.settings)
            )

            # make sure the related entity exists in the database
            # because the relationship cannot be stored otherwise
            if not related_entity_handler.select(related_entity.uid):
                logger.warning(
                    f"Related entity '{related_entity.uid}' does not exist in the database. Storing it first."
                )
                related_entity_handler.insert_many([related_entity])

            # now we can store the relationship
            # using the entity graph handler
            entity_handler = (
                FilmGraphHandler(self.settings)
                if isinstance(entity, Film)
                else PersonGraphHandler(self.settings)
            )

            if not entity_handler.select(entity.uid):
                logger.warning(
                    f"Entity '{entity.uid}' does not exist in the database. Storing it first."
                )
                entity_handler.insert_many([entity])

            logger.info(
                f"Storing relationship '{relationship.relation_type}' between '{entity.uid}' and '{related_entity.uid}'."
            )

            result = entity_handler.add_relationship(
                content=entity,
                relation_type=relationship.relation_type,
                related_content=related_entity,
            )

            logger.info(
                f"Relationship '{relationship.relation_type}' between '{entity.uid}' and '{related_entity.uid}' stored successfully."
            )

            return result

        else:
            logger.warning(
                f"Related entity for '{relationship.related_entity_name}' not found. Skipping relationship storage."
            )
        return None

    @task(task_run_name="analyze_relationships-{entity.uid}", cache_policy=NO_CACHE)
    def analyze_relationships(self, entity: Composable) -> Composable:
        """
        Analyze the relationships of a single entity.
        This method should be implemented to analyze the relationships
        and store them in the graph database.
        """

        logger = get_run_logger()

        _futures = []

        if self.entity_type == Film:

            # retrieve the persons that directed the film
            entity: Film = entity  # type: ignore

            if (
                entity.specifications is not None
                and entity.specifications.directed_by is not None
            ):

                for name in entity.specifications.directed_by:

                    _fut_relationship: PrefectFuture = self.do_enrichment.submit(
                        entity=entity,
                        relationship=RelationshipData(
                            related_entity_name=name,
                            relation_type=PeopleRelationshipType.DIRECTED_BY,
                        ),
                    )

                    _futures.append(_fut_relationship)

            # retrieve the persons that wrote the script of the film
            if (
                entity.specifications is not None
                and entity.specifications.written_by is not None
            ):

                for name in entity.specifications.written_by:

                    _fut_relationship: PrefectFuture = self.do_enrichment.submit(
                        entity=entity,
                        relationship=RelationshipData(
                            related_entity_name=name,
                            relation_type=PeopleRelationshipType.WRITTEN_BY,
                        ),
                    )

                    _futures.append(_fut_relationship)

            # retrieve the persons that composed the music of the film
            if (
                entity.specifications is not None
                and entity.specifications.music_by is not None
            ):

                for name in entity.specifications.music_by:

                    _fut_relationship: PrefectFuture = self.do_enrichment.submit(
                        entity=entity,
                        relationship=RelationshipData(
                            related_entity_name=name,
                            relation_type=PeopleRelationshipType.COMPOSED_BY,
                        ),
                    )

                    _futures.append(_fut_relationship)

            # retrieve the persons that influenced the film
            if entity.influences is not None and len(entity.influences) > 0:

                for influence in entity.influences:
                    for p in influence.persons:

                        _fut_relationship: PrefectFuture = self.do_enrichment.submit(
                            entity=entity,
                            relationship=RelationshipData(
                                related_entity_name=name,
                                relation_type=PeopleRelationshipType.INFLUENCED_BY,
                            ),
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

    @flow(
        name="execute_find_relationships",
    )
    def execute(
        self,
    ) -> None:

        logger = get_run_logger()

        local_storage_handler = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        try:

            # send concurrent tasks to analyze HTML content
            # don't wait for the task to be completed
            storage_futures = []

            # need to keep track of the futures to wait for them later
            # see: https://github.com/PrefectHQ/prefect/issues/17517
            entity_futures = []

            for entity in local_storage_handler.scan():

                logger.info(
                    f"Found entity '{entity.uid}' in json storage, launching analysis."
                )

                future_entity = self.analyze_relationships.submit(
                    entity=entity,
                )
                entity_futures.append(future_entity)

                # storage_futures.append(
                #     self.store_relationship.submit(
                #         # storage=json_p_storage,
                #         entity=future_entity,
                #     )
                # )

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
