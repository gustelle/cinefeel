import re

from bs4 import BeautifulSoup
from htmlrag import clean_html

from src.interfaces.nlp_processor import Processor


class HTMLSimplifier(Processor[str]):
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

        # replace <br> tags with newlines
        html_content = html_content.replace("<br>", "\n").replace("<br/>", "\n")

        # simplify the HTML content
        # for better embedding
        simplified_html = clean_html(html_content)

        # Remove notes like [1] or [2] from the content
        simplified_html = re.sub(r"\[\d+\]", "", simplified_html)

        # remove things like [modifier | modifier le code]
        simplified_html = re.sub(
            r"\[\s*modifier\s*\|\s*modifier\s+le\s+code\s*\]", "", simplified_html
        )

        replace_tags = [
            r"<time[^>]*>(.+)</time>",
            r"<code[^>]*>(.+)</code>",
            r"<pre[^>]*>(.+)</pre>",
            r"<blockquote[^>]*>(.+)</blockquote>",
            r"<a[^>]*>(.+)</a>",
            r"<span[^>]*>(.+)</span>",
            r"<small[^>]*>(.+)</small>",
            r"<b[^>]*>(.+)</b>",
            r"<i[^>]*>(.+)</i>",
            r"<strong[^>]*>(.+)</strong>",
            r"<em[^>]*>(.+)</em>",
            r"<sup[^>]*>(.+)</sup>",  # ex: Paris 10<sup>e</sup> arrondissement
            r"<sub[^>]*>(.+)</sub>",  # ex: Paris 10<sub>e</sub> arrondissement
        ]

        # pattern = r"|".join(replace_tags)

        for pattern in replace_tags:

            # remove <a> tags but keep the content inside
            matches = re.finditer(pattern, simplified_html, re.IGNORECASE)

            for m in matches:
                # need to go through bs4 to get the text content
                # because tags may contain other tags inside
                # and we want to keep the text content only
                # ex: <a href="..."><b>1864</b></a><a>Paris</a> should become "Example"
                content = BeautifulSoup(m.group(0), "html.parser").get_text(strip=False)
                simplified_html = simplified_html.replace(m.group(0), content)

        return simplified_html
