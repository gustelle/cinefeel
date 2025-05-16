from io import StringIO

import pandas as pd
import polars as pl
from interfaces.parser import ILinkExtractor


class WikipediaParsingError(Exception):
    pass


class WikipediaLinkExtractor(ILinkExtractor):
    """
    This class is responsible for parsing Wikipedia list of links to other pages.

    TODO:
        - rename this to WikipediaLinkExtractor
    """

    content: str

    def extract_links(
        self, html_content: str, attrs: dict, page_id: str | None = None
    ) -> list[str]:
        """
        Parses the given HTML content and returns a list of inner links to other interesting pages.
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

        Example:
        - https://api.wikimedia.org/core/v1/wikipedia/fr/page/Liste_de_films_fran%C3%A7ais_sortis_en_1907/html

        Args:
            html_content (str): _description_
            attrs (dict): _description_
            page_id (str | None, optional): _description_. Defaults to None.
                The page ID is used to identify the Wikipedia page from which the films are extracted.

        Returns:
            list[str]: a list of wikipedia page IDs (links) to other pages.

        Raises:
            WikipediaParsingError:
        """

        page_ids: list[str] = []

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

                page_ids.append(linked_page_id)
        except Exception as e:
            print(f"Error parsing HTML on '{page_id}': {e}")
            raise WikipediaParsingError(
                f"Failed to parse HTML on '{page_id}': {e}"
            ) from e

        return page_ids
