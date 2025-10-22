from __future__ import annotations

from loguru import logger
from pydantic import HttpUrl

from src.exceptions import RetrievalError
from src.interfaces.http_client import IHttpClient
from src.settings import Settings


def download_page(
    http_client: IHttpClient,
    page_id: str,
    settings: Settings,
    **params,
) -> str:
    """
    Pre-requisite: The class `http_client` provided must be synchronous (async not supported yet).

    Args:
        http_client (IHttpClient): The HTTP client to use for making requests.
        page_id (str): The page ID to download.
        settings (Settings): The application settings.
        **params: Additional parameters for the HTTP request.

    Returns:
        str: The HTML content of the downloaded page.
    """

    endpoint = f"{settings.mediawiki_base_url}/page/{page_id}/html"

    return http_client.send(
        url=endpoint,
        response_type="text",
        params=params,
    )


def get_permalink(name: str, http_client: IHttpClient) -> HttpUrl | None:
    """
    retrieves the permalink for a given Wikipedia page name.

    TODO:
    - test this function

    Example:
        >>> get_permalink("Some Wikipedia Page", http_client=http_client)
        # would be:
        # HttpUrl("https://fr.wikipedia.org/wiki/Some_Wikipedia_Page")

        >>> get_permalink("NonExistingPage", http_client=http_client)
        # would raise RetrievalError(...)

    Args:
        name (str): The name of the page to verify.

    Returns:
        str | None: the page ID of the page on Wikipedia, or None if not found.

    Raises:
        RetrievalError
    """

    try:

        if name is None or name.strip() == "":
            logger.warning(f"Invalid name provided: '{name}'")
            return None

        endpoint = f"https://fr.wikipedia.org/w/rest.php/v1/page/{name}/bare"
        response = http_client.send(
            url=endpoint,
            response_type="json",
        )
        page_id = response["key"]
        return HttpUrl(f"https://fr.wikipedia.org/wiki/{page_id}")

    except KeyError as e:
        raise RetrievalError(
            reason=f"Unexpected response structure when retrieving page ID for name '{name}': {str(e)}",
            status_code=500,
        ) from e


def get_page_id(permalink: HttpUrl) -> str:
    """Query wikipedia to get the page ID from a permalink.

    TODO:
    - test this function

    Args:
        permalink (HttpUrl): The permalink URL of the Wikipedia page.

    Returns:
        str: The extracted page ID.
    """
    try:
        # extract the page ID from the permalink
        return str(permalink).split("/wiki/")[-1]
    except Exception as e:
        raise RetrievalError(
            reason=f"Error extracting page ID from permalink '{permalink}': {str(e)}",
            status_code=500,
        ) from e
