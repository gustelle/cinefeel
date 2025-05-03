from io import StringIO

import pandas as pd
import polars as pl
from bs4 import BeautifulSoup
from entities.film import WikipediaFilm
from interfaces.parser import IParser


class WikipediaFilmSheetParser(IParser):

    content: str

    def extract_list(self, html_content: str, attrs: dict) -> list[WikipediaFilm]:
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

        Returns:
            list[WikipediaFilm]: _description_
        """

        films: list[WikipediaFilm] = []

        pd_df = pd.read_html(StringIO(html_content), extract_links="all", attrs=attrs)[
            0
        ]

        series = pl.from_pandas(pd_df).select(pl.first())

        for i in range(len(series)):

            if series[i, 0] is None or len(series[i, 0]) < 2 or series[i, 0][1] is None:
                continue

            page_id = series[i, 0][1].split("/")[-1]

            if page_id == "":
                continue

            films.append(
                WikipediaFilm(
                    title=series[i, 0][0],
                    work_of_art_id=page_id,
                )
            )

        return films

    def extract_film_info(
        self, film: WikipediaFilm, html_content: str
    ) -> WikipediaFilm:
        """
        Parses the given HTML content and returns the extracted attributes as a dictionary.

        Attributes can include the film director, date of release, distributor, and other relevant information.

        Args:
            html_content (str): The HTML content to parse.
            attrs (dict): The attributes to use for parsing the HTML content.
            The attributes can include the class name, id, or any other relevant attribute.

        TODO:
            - Add more attributes to the WikipediaFilm class.
            - Add more parsing logic to extract additional information from the HTML content.
            - Handle cases where the HTML structure may vary or be inconsistent.
            - Add error handling for cases where the HTML content is not as expected.
            - Consider using a more robust HTML parsing library if needed.

        """

        soup = BeautifulSoup(html_content, "html.parser")

        infobox = soup.find("div", "infobox")

        if infobox is None:
            print(f"Infobox not found for {film.work_of_art_id}")
            return film

        pd_df = pd.read_html(StringIO(infobox.decode()), extract_links="all")[0]

        # print(f"found details {pd_df}")
        # film.add_info(pd_df)

        return film
