from __future__ import annotations

from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE

from src.entities.content import PageLink, TableOfContents
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.info_retriever import IContentParser
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.db.local_storage.html_storage import LocalTextStorage
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.settings import Settings

from .retry import RETRY_ATTEMPTS, RETRY_DELAY_SECONDS, is_task_retriable


class ContentDownloaderTask(ITaskExecutor):
    """Downloads the HTML content of a page from a MediaWiki API and stores it using the provided storage handler."""

    settings: Settings
    http_client: IHttpClient

    # the endpoint to download the page content
    # ex: https://en.wikipedia.org/api/rest_v1/page/{page_id}/html
    _endpoint_template: str

    def __init__(self, settings: Settings, http_client: IHttpClient):
        self.settings = settings
        self.http_client = http_client
        self._endpoint_template = (
            f"{self.settings.mediawiki_base_url}/page/{{page_id}}/html"
        )

    @task(
        task_run_name="download-{page_id}",
        retries=RETRY_ATTEMPTS,
        retry_delay_seconds=RETRY_DELAY_SECONDS,
        retry_condition_fn=is_task_retriable,
        cache_policy=NO_CACHE,
        tags=["cinefeel_tasks"],
    )
    def download(
        self,
        page_id: str,
        storage_handler: LocalTextStorage | None = None,
        return_content: bool = False,
        **params,
    ) -> str | None:
        """
        Pre-requisite: The class `http_client` provided must be synchronous (async not supported yet).

        Args:
            page_id (str): The page ID to download.
            storage_handler (LocalTextStorage | None, optional): The storage handler to use for storing the content. Defaults to None.
            return_content (bool, optional): Whether to return the content. Defaults to False, in which case the content ID is returned.
            **params: Additional parameters for the HTTP request.

        Returns:
            str | None: The content ID if the download was successful, None otherwise.
        """

        endpoint = self._endpoint_template.format(page_id=page_id)

        get_run_logger().info(f">> Downloading '{endpoint}'")

        try:
            html = self.http_client.send(
                url=endpoint,
                response_type="text",
                params=params,
            )
        except HttpError as e:
            if e.status_code == 404:
                get_run_logger().warning(
                    f"Page '{page_id}' not found at '{endpoint}'. Skipping download."
                )
                return None
            else:
                # force a retry for other HTTP errors
                raise

        if html is not None and storage_handler is not None:
            storage_handler.insert(
                content_id=page_id,
                content=html,
            )
        if return_content:
            return html

        return page_id if html is not None else None

    @task(cache_policy=NO_CACHE, tags=["cinefeel_tasks"])
    def extract_page_links(
        self,
        config: TableOfContents,
        link_extractor: IContentParser,
    ) -> list[PageLink]:
        """
        downloads the HTML page and extracts the links from it.

        Args:
            page (WikiTOCPageConfig): The configuration for the page to be downloaded.

        Returns:
            list[PageLink]: A list of page links.
        """

        logger = get_run_logger()

        html = self.download(
            page_id=config.page_id,
            return_content=True,  # return the content
        )

        if html is None:
            return []

        try:

            _links = link_extractor.retrieve_inner_links(
                html_content=html,
                config=config,
            )

            return _links

        except Exception as e:
            logger.error(f"Error extracting list of movies: {e}")
            return []

    @task(
        cache_policy=NO_CACHE, retries=3, retry_delay_seconds=5, tags=["cinefeel_tasks"]
    )
    def execute(
        self,
        page: PageLink,
        storage_handler: IStorageHandler,
        link_extractor: IContentParser | None = WikipediaParser(),
        return_results: bool = False,
    ) -> list[str] | None:
        """
        runs the task to download the HTML content of a page and store it using the provided storage handler.
        - If the `page` is a `TableOfContents`, it will first extract the links from the table of contents
        and then download each linked page.
        - If the `page` is a `PageLink`, it will directly download the page.

        Args:
            page (PageLink): The permalink to the page to be downloaded.
            storage_handler (IStorageHandler): the storage handler to use for storing the content that is downloaded.
            link_extractor (IContentParser | None, optional): The link extractor to use for extracting links from a table of contents.
                Defaults to WikipediaParser().
            return_results (bool, optional): Defaults to False.

        Returns:
            list[str] | None: a list of `page_id` stored into the storage backend
                if `return_results` is set to True, else None
        """

        if isinstance(page, TableOfContents):
            # extract the links from the table of contents
            page_links = self.extract_page_links(
                config=page,
                link_extractor=link_extractor,
            )
        else:
            page_links = [page]

        content_ids = [
            self.download(
                page_id=page_link.page_id,
                storage_handler=storage_handler,
                return_content=False,  # for memory constraints, return the content ID
            )
            for page_link in page_links
            if isinstance(page_link, PageLink)
        ]

        # filter out None values
        content_ids = [cid for cid in content_ids if cid is not None]

        if return_results:
            return content_ids
