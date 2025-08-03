from __future__ import annotations

from prefect import get_run_logger, task
from prefect.cache_policies import NO_CACHE

from src.entities.content import PageLink
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.info_retriever import IContentParser
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.db.local_storage.html_storage import LocalTextStorage
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.settings import Settings, TableOfContents

from .retry import is_task_retriable


class PageContentDownloader(ITaskExecutor):

    settings: Settings
    http_client: IHttpClient
    page_endpoint: str

    def __init__(self, settings: Settings, http_client: IHttpClient):
        self.settings = settings
        self.http_client = http_client
        self.page_endpoint = f"{self.settings.mediawiki_base_url}/page/{{page_id}}/html"

    @task(
        task_run_name="download-{page_id}",
        retries=3,
        retry_delay_seconds=[1, 2, 5],
        retry_condition_fn=is_task_retriable,
        cache_policy=NO_CACHE,
    )
    def download(
        self,
        page_id: str,
        storage_handler: LocalTextStorage | None = None,
        return_content: bool = False,
        **params,
    ) -> str | None:
        """
        Pre-requisite: The class `http_client` provided must be synchronous.

        Args:
            page_id (str): The page ID to download.
            storage_handler (HtmlContentStorageHandler | None, optional): The storage handler to use for storing the content. Defaults to None.
            return_content (bool, optional): Whether to return the content. Defaults to False, in which case the content ID is returned.
            **params: Additional parameters for the HTTP request.

        Returns:
            str | None: The content ID if the download was successful, None otherwise.
        """

        endpoint = self.page_endpoint.format(page_id=page_id)

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
                get_run_logger().error(
                    f"Server error while downloading '{endpoint}': {e.status_code}"
                )
                raise

        if html is not None and storage_handler is not None:
            storage_handler.insert(
                content_id=page_id,
                content=html,
            )
        if return_content:
            return html

        return page_id if html is not None else None

    @task(cache_policy=NO_CACHE)
    def fetch_page_links(
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

        html = self.download.submit(
            page_id=config.page_id,
            return_content=True,  # return the content
        ).result(timeout=self.settings.prefect_task_timeout, raise_on_failure=True)

        if html is None:
            return []

        try:

            _links = link_extractor.retrieve_inner_links(
                html_content=html,
                config=config,
            )

            return _links

        except Exception as e:
            logger.error(f"Error extracting list of films: {e}")
            return []

    def execute(
        self,
        page: PageLink,
        storage_handler: IStorageHandler,
        return_results: bool = False,
    ) -> list[str] | None:
        """

        Args:
            page (PageLink): The permalink to the page to be downloaded.
            storage_handler (IStorageHandler): the storage handler to use for storing the content that is downloaded.
            return_results (bool, optional): Defaults to False.

        Returns:
            list[str] | None:
        """

        if isinstance(page, TableOfContents):
            # extract the links from the table of contents
            link_extractor = WikipediaParser()
            page_links = self.fetch_page_links(
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
