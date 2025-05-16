import re

from entities.film import Film
from interfaces.analyzer import IContentAnalyzer
from interfaces.content_parser import IContentParser
from interfaces.similarity import ISimilaritySearch
from loguru import logger

from .bert_similarity import BertSimilaritySearch
from .html_splitter import HtmlParser, HtmlSection
from .ollama_parser import OllamaParser


class HtmlContentAnalyzer(IContentAnalyzer):

    film_parser: IContentParser
    simiarity_search: ISimilaritySearch

    def __init__(
        self,
    ):
        """
        Initializes the HtmlAnalyzer with a ChromaDB client.

        Args:
            client (chromadb.Client, optional): A ChromaDB client instance.
                Defaults to None, which creates an ephemeral client.
        """
        self.film_parser = OllamaParser[Film]()
        self.simiarity_search = BertSimilaritySearch()

    def find_tech_spec(
        self,
        sections: list[HtmlSection],
    ) -> HtmlSection | None:

        most_similar_section = None

        for text_query in ["fiche technique", "synopsis", "résumé"]:

            # score = section_title_query_result.points[0].score
            most_similar_section_title = self.simiarity_search.most_similar(
                query=text_query,
                corpus=[section.title for section in sections],
            )

            if most_similar_section_title is None:
                continue

            pattern = re.compile(rf"\s*{text_query}\s*", re.IGNORECASE)

            most_similar_sections = [
                section for section in sections if pattern.match(section.title)
            ]

            if len(most_similar_sections) == 0:
                logger.warning(
                    f"no section found for '{text_query}' (found '{most_similar_section_title}')"
                )
                continue

            most_similar_section = most_similar_sections[0]

            if (
                most_similar_section is None
                or most_similar_section.content is None
                or len(most_similar_section.content) == 0
            ):
                logger.warning(
                    f"content of section '{most_similar_section_title}' is empty"
                )
                continue

            break

        return most_similar_section

    def analyze(self, html_content: str) -> Film | None:
        """
        TODO:
        - split the content into sentences
        - vectorize the content
        - use a llm to find the most relevant entity, genre, themes, etc.
        - scrape the content according to the entity type
        """

        logger.info("-" * 80)

        splitter = HtmlParser()

        # split the HTML content into sections
        sections = splitter.split_sections(html_content)

        if sections is None or len(sections) == 0:
            logger.warning("no sections found, skipping the content")
            return None

        tech_spec = self.find_tech_spec(
            sections=sections,
        )

        if tech_spec is None or tech_spec.content is None:

            info_table = splitter.parse_info_table(html_content)
            if info_table is None or len(info_table) == 0:
                logger.warning("no info table found, skipping the content")
                return None

            logger.info(f"found {len(info_table)} info table elements")

            # convert the DataFrame to a string
            ctx = "\n".join([f"{row.title}: {row.content}" for row in info_table])
            logger.info(f"Context is '{ctx}'")

        else:
            ctx = tech_spec.content

        logger.info(f"Context is '{ctx}'")

        question = "Give information about the film "

        resp = self.film_parser.to_entity(
            context=ctx,
            question=question,
        )

        logger.info(f"response : '{resp.model_dump_json()}'")

        return resp


# class WikipediaFilmParser(IPageParser[Film]):

#     content: str

#     def enrich(self, film: Film, html_content: str) -> Film:
#         """
#         Parses the given HTML content and returns the extracted attributes as a dictionary.

#         Attributes can include the film director, date of release, distributor, and other relevant information.

#         Args:
#             film (WikipediaFilm): The WikipediaFilm object to populate with extracted attributes.
#             html_content (str): The HTML content to parse.

#         Returns:
#             WikipediaFilm: The WikipediaFilm object populated with extracted attributes.

#         Raises:
#             WikipediaFilmParserError: If there is an error while parsing the HTML content.

#         TODO:
#             - Add more attributes to the WikipediaFilm class.
#             - Add more parsing logic to extract additional information from the HTML content.
#             - Handle cases where the HTML structure may vary or be inconsistent.
#             - Add error handling for cases where the HTML content is not as expected.
#             - Consider using a more robust HTML parsing library if needed.

#         """
#         try:

#             soup = BeautifulSoup(html_content, "html.parser")

#             infobox = soup.find("div", "infobox")

#             if infobox is None:
#                 logger.info(f"Infobox not found for {film.work_of_art_id}")
#                 return film

#             _ = pd.read_html(StringIO(infobox.decode()), extract_links="all")[0]

#             # logger.info(f"found details {pd_df}")
#             # film.add_info(pd_df)

#             return film

#         except Exception as e:
#             logger.info(f"Error parsing HTML content: {e}")

#             raise WikipediaParsingError(f"Failed to parse HTML content: {e}") from e


# class WikipediaPersonParser(IPageParser[Person]):

#     content: str

#     def enrich(self, person: Person, html_content: str) -> Film:
#         # TODO

#         return person
