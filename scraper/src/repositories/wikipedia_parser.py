from io import StringIO

import pandas as pd
import polars as pl
from bs4 import BeautifulSoup
from entities.film import Film
from interfaces.parser import IParser


class WikipediaFilmParserError(Exception):
    pass


class WikipediaFilmParser(IParser):

    content: str

    def extract_films_list(
        self, html_content: str, attrs: dict, page_id: str | None = None
    ) -> list[Film]:
        """
        Parses the given HTML content and returns a list of WikipediaFilm objects.
        The HTML content is expected to contain a table with film titles and links.
        The table should have the following structure:
        ```
        <table class="wikitable">
            <tr>
                <th>Title</th>
                <th>Link</th>
            </tr>
            <tr>
                <td><a href="/wiki/Film_Title">Film Title</a></td>
                <td>Link to film page</td>
            </tr>
        </table>
        ```

        Args:
            html_content (str): _description_
            attrs (dict): _description_
            page_id (str | None, optional): _description_. Defaults to None.
                The page ID is used to identify the Wikipedia page from which the films are extracted.

        Returns:
            list[WikipediaFilm]: _description_

        Raises:
            WikipediaFilmParserError: _description_
        """

        films: list[Film] = []

        try:

            pd_df = pd.read_html(
                StringIO(html_content), extract_links="all", attrs=attrs
            )[0]

            if "1914" in page_id:
                print(f"found details {pd_df}")

            series = pl.from_pandas(pd_df).select(pl.first())

            for i in range(len(series)):

                if (
                    series[i, 0] is None
                    or len(series[i, 0]) < 2
                    or series[i, 0][1] is None
                ):
                    continue

                linked_page_id = series[i, 0][1].split("/")[-1]

                if linked_page_id == "":
                    continue

                films.append(
                    Film(
                        title=series[i, 0][0],
                        work_of_art_id=linked_page_id,
                    )
                )
        except Exception as e:
            print(f"Error parsing HTML on '{page_id}': {e}")
            raise WikipediaFilmParserError(
                f"Failed to parse HTML on '{page_id}': {e}"
            ) from e

        return films

    def extract_film_details(self, film: Film, html_content: str) -> Film:
        """
        Parses the given HTML content and returns the extracted attributes as a dictionary.

        Attributes can include the film director, date of release, distributor, and other relevant information.

        Args:
            film (WikipediaFilm): The WikipediaFilm object to populate with extracted attributes.
            html_content (str): The HTML content to parse.

        Returns:
            WikipediaFilm: The WikipediaFilm object populated with extracted attributes.

        Raises:
            WikipediaFilmParserError: If there is an error while parsing the HTML content.

        TODO:
            - Add more attributes to the WikipediaFilm class.
            - Add more parsing logic to extract additional information from the HTML content.
            - Handle cases where the HTML structure may vary or be inconsistent.
            - Add error handling for cases where the HTML content is not as expected.
            - Consider using a more robust HTML parsing library if needed.

        """
        try:

            soup = BeautifulSoup(html_content, "html.parser")

            infobox = soup.find("div", "infobox")

            if infobox is None:
                print(f"Infobox not found for {film.work_of_art_id}")
                return film

            _ = pd.read_html(StringIO(infobox.decode()), extract_links="all")[0]

            # print(f"found details {pd_df}")
            # film.add_info(pd_df)

            return film

        except Exception as e:
            print(f"Error parsing HTML content: {e}")

            raise WikipediaFilmParserError(f"Failed to parse HTML content: {e}") from e
