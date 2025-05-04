import asyncio

from entities.film import Film
from interfaces.data_source import IDataSource
from interfaces.http_client import IHttpClient, ScrapingError
from interfaces.parser import IParser
from interfaces.task_runner import ITaskRunner
from settings import Settings


class WikipediaCrawler(IDataSource):
    """
    this class is responsible for scraping Wikipedia pages and extracting film information.

    It must be used in a context manager to ensure that the scraper is closed properly.

    Example:
    ```python
        async with WikipediaRepository(...) as wiki_repo:
            films = await wiki_repo.crawl()
    ```
    """

    settings: Settings

    page_endpoint: str = "page/"
    parser: IParser
    async_task_runner: ITaskRunner

    def __init__(
        self,
        http_client: IHttpClient,
        parser: IParser,
        settings: Settings,
        task_runner: ITaskRunner,
    ):
        super().__init__(scraper=http_client)
        self.parser = parser
        self.settings = settings
        self.async_task_runner = task_runner

    async def get_page_content(self, page_id: str, **params) -> str | None:
        """
        Get raw HTML from the Wikipedia API.

        Args:
            page_id (str): The ID of the page to retrieve.
            **params: Additional parameters to pass to the API.
        """

        try:
            endpoint = (
                f"{self.settings.mediawiki_base_url}/{self.page_endpoint}{page_id}/html"
            )

            return await self.scraper.send(
                endpoint=endpoint,
                response_type="text",
                params=params,
            )
        except ScrapingError as e:
            if e.status_code == 404:
                print(f"Page '{page_id}' not found")
            return None

    async def get_films(self, page_list_id: str) -> list[Film]:
        """
        Get the sections of a Wikipedia page.

        Args:
            page_list_id (str): The ID of the page containing the list of films.

        Returns:
            list[WikipediaFilm]: A list of WikipediaFilm objects containing the title and link to the film page.
        """

        html = await self.get_page_content(page_id=page_list_id)

        if html is None:
            return []

        # extract the list of films from the HTML
        try:
            films: list[Film] = await self.async_task_runner.submit(
                self.parser.extract_list,
                html_content=html,
                attrs={
                    "class": "wikitable",
                },
                page_id=page_list_id,
            )
        except Exception as e:
            print(f"Error extracting list of films: {e}")
            return []

        # for each film, get the details
        details_tasks = [
            self.get_page_content(page_id=film.work_of_art_id) for film in films
        ]

        results = await asyncio.gather(*details_tasks)

        final_films = []

        for i, details in enumerate(results):

            if details is None:
                continue

            # get the details from the page
            try:

                film: Film = await self.async_task_runner.submit(
                    self.parser.extract_film_info,
                    film=films[i],  # retrieve the film object !
                    html_content=details,
                )

                print(f"Found details for film '{film.title}'")
                final_films.append(film)
            except Exception as e:
                print(f"Error parsing film info: {e}")
                continue

        return final_films

    async def crawl(self) -> list[Film]:
        """
        Crawl the Wikipedia page and return a list of films.

        Returns:
            list[WikipediaFilm]: A list of WikipediaFilm objects containing the title and link to the film page.
        """

        tasks = []

        for year in range(1907, 1910):

            tasks.append(
                self.get_films(
                    page_list_id=f"Liste_de_films_français_sortis_en_{year}",
                )
            )

        # wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        if any(isinstance(result, Exception) for result in results):
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error: {result}")

        return [
            film
            for result in results
            for film in result
            if not isinstance(result, Exception)
        ]  # flatten the list

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.scraper.close()
