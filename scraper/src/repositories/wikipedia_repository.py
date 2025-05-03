import asyncio

from entities.film import WikipediaFilm
from interfaces.data_source import IDataSource
from interfaces.parser import IParser
from interfaces.scraper import IScraper, ScrapingError


class WikipediaRepository(IDataSource):

    _base_url: str = "https://api.wikimedia.org/core/v1/wikipedia/fr/"
    _ua = "Cinefeel"

    page_endpoint: str = "page/"
    parser: IParser

    def __init__(self, scraper: IScraper, parser: IParser):
        super().__init__(scraper=scraper)
        self.parser = parser

    async def get_page_content(self, page_id: str, **params) -> str | None:
        """
        Get raw HTML from the Wikipedia API.

        Args:
            page_id (str): The ID of the page to retrieve.
            **params: Additional parameters to pass to the API.
        """

        try:
            endpoint = f"{self._base_url}{self.page_endpoint}{page_id}/html"

            return await self.scraper.scrape(
                endpoint=endpoint,
                response_type="text",
                params=params,
                headers={
                    "User-Agent": self._ua,
                },
            )
        except ScrapingError as e:
            if e.status_code == 404:
                print(f"Page '{page_id}' not found")
            return None

    async def get_films(self, page_list_id: str) -> list[WikipediaFilm]:
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

        films = self.parser.extract_list(
            html_content=html,
            attrs={
                "class": "wikitable",
            },
        )

        print(f"Found {len(films)} links on page {page_list_id}")

        # for each film, get the details
        details_tasks = [
            self.get_page_content(page_id=film.work_of_art_id) for film in films
        ]

        results = await asyncio.gather(*details_tasks)

        for i, details in enumerate(results):

            if details is None:
                continue

            film = self.parser.extract_film_info(
                film=films[i],
                html_content=details,
            )

            print(f"Found details for film '{film.title}'")

        return films

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.scraper.close()
