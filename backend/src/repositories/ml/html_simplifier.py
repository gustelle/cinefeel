from htmlrag import clean_html

from src.interfaces.similarity import MLProcessor


class HTMLSimplifier(MLProcessor[str]):
    """
    Simplifies the HTML content by removing unnecessary tags and attributes.

    TODO:
    - remove the notes like [1] or [2] from the content.
    - remove things like [modifier | modifier le code]
    - remove also subsections titles from the content, like "Vie privée" or "Filmographie".
    """

    """
    Splits a given HTML content into sections based on the specified tags.
    """

    def process(
        self,
        html_content: str,
    ) -> str:
        """
        Splits the HTML content into sections based on the specified tags.

        the sections rendered are simplified using `htmlrag` to remove unnecessary scripts and styles
        and to make the text easier for embedding.

        Args:
            html_content (str): The HTML content to be processed.

        Returns:
            str: A simplified version of the HTML content, with unnecessary tags and attributes removed.
        """

        # simplify the HTML content
        # for better embedding
        simplified_html = clean_html(html_content)

        return simplified_html
