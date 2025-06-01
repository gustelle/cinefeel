import re

from htmlrag import clean_html

from src.interfaces.similarity import MLProcessor


class HTMLSimplifier(MLProcessor[str]):
    """
    Simplifies the HTML content by removing unnecessary tags and attributes.
    """

    def process(
        self,
        html_content: str,
    ) -> str:
        """
        Processes the given HTML content to simplify it for better embedding and information retrieval by LLMs

        - JavaScript and CSS are removed, and unnecessary notes or modifiers are stripped out.
        - Information wrapped by <a> tags is preserved, but the tags themselves are removed.

        Args:
            html_content (str): The HTML content to be processed.

        Returns:
            str: A simplified version of the HTML content, with unnecessary tags and attributes removed.
        """

        # simplify the HTML content
        # for better embedding
        simplified_html = clean_html(html_content)

        # Remove notes like [1] or [2] from the content
        simplified_html = re.sub(r"\[\d+\]", "", simplified_html)

        # remove things like [modifier | modifier le code]
        simplified_html = re.sub(
            r"\[\s*modifier\s*\|\s*modifier\s+le\s+code\s*\]", "", simplified_html
        )

        matches = re.finditer(r"<a[^>]*>(.+)</a>", simplified_html, re.IGNORECASE)

        for m in matches:
            content = m.group(1)  # Get the content inside the <a> tag
            # logger.debug(f"Replacing '{m.group(0)}' by '{content}'")
            simplified_html = simplified_html.replace(m.group(0), content)

        return simplified_html
