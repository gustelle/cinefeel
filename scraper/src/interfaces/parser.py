from typing import Protocol

from entities.film import Film


class IParser(Protocol):
    """
    Interface for a parser that extracts data from a given HTML content.
    """

    def extract_list(self, html_content: str, *args, **kwargs) -> list[Film]:
        """
        Parses the given HTML content and returns a list of WikipediaFilm objects.

        Args:
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            list[WikipediaFilm]: A list of WikipediaFilm objects containing the title and link to the film page.
        """
        pass

    def extract_film_info(
        self,
        film: Film,
        html_content: str,
        *args,
        **kwargs,
    ) -> Film:
        """
        Parses the given HTML content and returns the extracted attributes as a dictionary.

        Attributes can include the film director, date of release, distributor, and other relevant information.

        Args:
            film (WikipediaFilm): The WikipediaFilm object to update.
            html_content (str): The HTML content to parse.
            *args: Additional arguments to pass to the parser.
            **kwargs: Additional keyword arguments to pass to the parser.

        Returns:
            WikipediaFilm: The updated WikipediaFilm object with the extracted attributes.

        """
        pass
