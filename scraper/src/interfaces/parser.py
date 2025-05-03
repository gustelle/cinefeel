from typing import Protocol

from entities.film import WikipediaFilm


class IParser(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def extract_list(self, html_content: str, attrs: dict) -> list[WikipediaFilm]:
        """
        Parses the given HTML content and returns a list of WikipediaFilm objects.

        Args:
            html_content (str): The HTML content to parse.
            attrs (dict): The attributes to use for parsing the HTML content.
            The attributes can include the class name, id, or any other relevant attribute.

        Returns:
            list[WikipediaFilm]: A list of WikipediaFilm objects containing the title and link to the film page.
        """
        pass

    def extract_film_info(
        self,
        film: WikipediaFilm,
        html_content: str,
    ) -> WikipediaFilm:
        """
        Parses the given HTML content and returns the extracted attributes as a dictionary.

        Attributes can include the film director, date of release, distributor, and other relevant information.

        Args:
            film (WikipediaFilm): The WikipediaFilm object to update.
            html_content (str): The HTML content to parse.

        Returns:
            WikipediaFilm: The updated WikipediaFilm object with the extracted attributes.

        """
        pass
