import asyncio
from typing import Any

from prefect import Task, flow, get_run_logger, task
from prefect.cache_policies import NO_CACHE
from prefect.client.schemas.objects import TaskRun
from prefect.states import State

from src.entities.content import PageLink
from src.interfaces.http_client import HttpError, IHttpClient
from src.interfaces.info_retriever import IContentParser
from src.interfaces.storage import IStorageHandler
from src.interfaces.task import ITaskExecutor
from src.repositories.html_parser.wikipedia_info_retriever import WikipediaParser
from src.repositories.local_storage.html_storage import LocalTextStorage
from src.settings import Settings, WikiTOCPageConfig


async def is_async_task_retriable(
    task: Task[..., Any], task_run: TaskRun, state: State[Any]
) -> bool:
    logger = get_run_logger()
    try:
        await state.result()
    except Exception as e:
        if isinstance(e, HttpError) and e.status_code >= 429:
            return True
        elif isinstance(e, HttpError):
            logger.warning(
                f"HTTP error with status {e.status_code} will not be retried"
            )
            return False
        else:
            logger.error(f"Exception is not retriable: {e}")
    return False


def is_task_retriable(
    task: Task[..., Any], task_run: TaskRun, state: State[Any]
) -> bool:
    logger = get_run_logger()
    try:
        state.result()
    except Exception as e:
        if isinstance(e, HttpError) and e.status_code >= 429:
            return True
        elif isinstance(e, HttpError):
            logger.warning(
                f"HTTP error with status {e.status_code} will not be retried"
            )
            return False
        else:
            logger.error(f"Exception is not retriable: {e}")
    return False


class DownloaderFlow(ITaskExecutor):

    settings: Settings
    http_client: IHttpClient
    page_endpoint: str

    def __init__(self, settings: Settings, http_client: IHttpClient):
        self.settings = settings
        self.http_client = http_client
        self.page_endpoint = f"{self.settings.mediawiki_base_url}/page/{{page_id}}/html"

    @task(
        task_run_name="async_download-{page_id}",
        retries=3,
        retry_delay_seconds=[1, 2, 5],
        retry_condition_fn=is_async_task_retriable,
        cache_policy=NO_CACHE,
    )
    async def async_download(
        self,
        page_id: str,
        storage_handler: LocalTextStorage | None = None,
        return_content: bool = False,
        **params,
    ) -> str | None:
        """
        Pre-requisite: The HttpClient must be asynchronous.

        Args:
            page_id (str): The page ID to download.
            storage_handler (HtmlContentStorageHandler | None, optional): The storage handler to use for storing the content. Defaults to None.
            return_content (bool, optional): Whether to return the content. Defaults to False, in which case the content ID is returned.
            **params: Additional parameters for the HTTP request.

        Returns:
            str | None: The content ID if the download was successful, None otherwise.
        """

        endpoint = self.page_endpoint.format(page_id=page_id)

        html = await self.http_client.send(
            url=endpoint,
            response_type="text",
            params=params,
        )

        if html is not None and storage_handler is not None:
            storage_handler.insert(
                content_id=page_id,
                content=html,
            )
        if return_content:
            return html

        return page_id if html is not None else None

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
        Pre-requisite: The HttpClient must be synchronous.

        Args:
            page_id (str): The page ID to download.
            storage_handler (HtmlContentStorageHandler | None, optional): The storage handler to use for storing the content. Defaults to None.
            return_content (bool, optional): Whether to return the content. Defaults to False, in which case the content ID is returned.
            **params: Additional parameters for the HTTP request.

        Returns:
            str | None: The content ID if the download was successful, None otherwise.
        """

        endpoint = self.page_endpoint.format(page_id=page_id)

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
        if return_content:
            return html

        return page_id if html is not None else None

    @task(cache_policy=NO_CACHE)
    async def fetch_page_links(
        self,
        config: WikiTOCPageConfig,
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

        html = await self.async_download(
            page_id=config.page_id,
            return_content=True,  # return the content
        )

        if html is None:
            return []

        # avoid blocking the event loop by using asyncio.to_thread
        try:
            _links = await asyncio.to_thread(
                link_extractor.retrieve_inner_links,
                html_content=html,
                config=config,
            )

            return _links

        except Exception as e:
            logger.error(f"Error extracting list of films: {e}")
            return []

    @flow(
        name="download",
    )
    async def execute(
        self,
        start_page: WikiTOCPageConfig,
        storage_handler: IStorageHandler,
        return_results: bool = False,
    ) -> list[str] | None:
        """

        Args:
            start_page (WikiTOCPageConfig):
            storage_handler (IStorageHandler): the storage handler to use for storing the content that is downloaded.
            return_results (bool, optional): Defaults to False.

        Returns:
            list[str] | None:
        """

        logger = get_run_logger()

        link_extractor = WikipediaParser()

        page_links = await self.fetch_page_links(
            config=start_page,
            link_extractor=link_extractor,
        )

        content_ids = await asyncio.gather(
            *[
                self.async_download(
                    page_id=page_link.page_id,
                    storage_handler=storage_handler,
                    return_content=False,  # for memory constraints, return the content ID
                )
                for page_link in page_links
                if isinstance(page_link, PageLink)
            ],
            return_exceptions=True,
        )

        content_ids = [cid for cid in content_ids if isinstance(cid, str)]

        logger.info("'download' flow completed successfully.")

        if return_results:
            return content_ids
