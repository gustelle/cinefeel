import dask
from prefect import flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.futures import PrefectFuture, wait

from src.entities.composable import Composable
from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.task import ITaskExecutor
from src.repositories.local_storage.html_storage import LocalTextStorage
from src.repositories.local_storage.json_storage import JSONEntityStorageHandler
from src.settings import Settings


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

        get_run_logger().info(
            f"Initialized RelationshipFlow, http_client: {http_client}"
        )

    @task(
        task_run_name="download_relationship_page-{page_id}",
        retries=3,
        retry_delay_seconds=[1, 2, 5],
        cache_policy=NO_CACHE,
    )
    def download_person_page(
        self,
        page_id: str,
        storage_handler: LocalTextStorage | None = None,
        **params,
    ) -> str | None:
        """


        Args:
            page_id (str): The page ID to download.
            storage_handler (HtmlContentStorageHandler | None, optional): The storage handler to use for storing the content. Defaults to None.
            **params: Additional parameters for the HTTP request.

        Returns:
            str | None: The content ID if the download was successful, None otherwise.
        """

        logger = get_run_logger()

        # 1. check if the page_id is already stored in the storage_handler
        # in which case we return the page_id
        if storage_handler is not None and storage_handler.select(content_id=page_id):
            logger.info(f"Page '{page_id}' already exists in storage.")
            return page_id

        endpoint = f"{self.settings.mediawiki_base_url}/page/{page_id}/html"

        try:

            logger = get_run_logger()
            logger.info(f"Downloading page {page_id} from {endpoint}")

            html = self.http_client.send(
                url=endpoint,
                response_type="text",
                params=params,
            )

            if html is not None and storage_handler is not None:
                storage_handler.insert(
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

    @task(
        task_run_name="search_person-{name}",
        retries=3,
        retry_delay_seconds=[1, 2, 5],
        cache_policy=NO_CACHE,
    )
    def search_person(
        self,
        name: str,
    ) -> str | None:
        """
        Returns:
            str | None: the page ID if the search was successful, None otherwise.
        """

        try:
            endpoint = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"
            response = self.http_client.send(
                url=endpoint,
                response_type="json",
            )
            return response["key"]
        except KeyError:
            return None

    @task(task_run_name="to_db-{entity.uid}", cache_policy=NO_CACHE)
    def to_db(self, entity: Composable) -> Composable:
        """
        Analyze the relationships of a single entity.
        This method should be implemented to analyze the relationships
        and store them in the graph database.
        """
        logger = get_run_logger()
        logger.info(f"Storing {entity.uid} into the graph database")

        # Here you would implement the logic to analyze relationships
        # For example, you might query a graph database or perform some analysis
        # and then store the results back into the graph database.
        return entity

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
            # retrieve the persons that influenced the film
            ...
            # retrieve the persons that directed the film
            entity: Film = entity  # type: ignore
            logger.info(
                f"Analyzing relationships for '{entity.uid}' (specifications {entity.specifications})"
            )

            html_storage = LocalTextStorage(
                path=self.settings.persistence_directory,
                entity_type=Person,
            )

            if (
                entity.specifications is not None
                and entity.specifications.directed_by is not None
            ):

                for name in entity.specifications.directed_by:

                    _fut_p = self.search_person.submit(name=name)

                    # keep track of the future to wait for it later
                    _futures.append(_fut_p)

                    # 1. query https://fr.wikipedia.org/w/rest.php/v1/page/James_cameron/bare and get the key (ex: "James_cameron")
                    # 2. download the HTML page of the person
                    _futures.append(
                        self.download_person_page.submit(
                            page_id=_fut_p,
                            storage_handler=html_storage,
                        )
                    )

            wait(
                _futures,
            )

            # retrieve the persons that wrote the script of the film
            ...
            # retrieve the persons that composed the music of the film
            ...
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

        return entity

    @flow(
        name="find_relationships",
    )
    def execute(
        self,
    ) -> None:

        logger = get_run_logger()

        local_storage_handler = JSONEntityStorageHandler[self.entity_type](
            settings=self.settings
        )

        # send concurrent tasks to analyze HTML content
        # don't wait for the task to be completed
        storage_futures = []

        # need to keep track of the futures to wait for them later
        # see: https://github.com/PrefectHQ/prefect/issues/17517
        entity_futures = []

        # analyze the HTML content
        with (
            dask.annotate(resources={"GPU": 1}),
            dask.config.set({"array.chunk-size": "512 MiB"}),
        ):

            for entity in local_storage_handler.scan():

                future_entity = self.analyze_relationships.submit(
                    entity=entity,
                )
                entity_futures.append(future_entity)

                storage_futures.append(
                    self.to_db.submit(
                        # storage=json_p_storage,
                        entity=future_entity,
                    )
                )

            # now wait for all tasks to complete
            future_storage: PrefectFuture
            for future_storage in storage_futures:
                try:
                    future_storage.result(
                        raise_on_failure=True, timeout=self.settings.task_timeout
                    )
                except TimeoutError:
                    logger.warning(f"Task timed out for {future_storage.task_run_id}.")
                except Exception as e:
                    logger.error(f"Error in task execution: {e}")

        # Iterate over the batch
        # pass the batch to the graph database
        # and insert it
