from interfaces.analyzer import ContentAnalysisError, IContentAnalyzer


class HtmlAnalyzer(IContentAnalyzer):

    def analyze(self, html_content: str):
        """
        TODO:
        - split the content into sentences
        - vectorize the content
        - use a llm to find the most relevant entity, genre, themes, etc.
        - scrape the content according to the entity type
        """

        # Placeholder for HTML analysis logic
        return None


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
#                 print(f"Infobox not found for {film.work_of_art_id}")
#                 return film

#             _ = pd.read_html(StringIO(infobox.decode()), extract_links="all")[0]

#             # print(f"found details {pd_df}")
#             # film.add_info(pd_df)

#             return film

#         except Exception as e:
#             print(f"Error parsing HTML content: {e}")

#             raise WikipediaParsingError(f"Failed to parse HTML content: {e}") from e


# class WikipediaPersonParser(IPageParser[Person]):

#     content: str

#     def enrich(self, person: Person, html_content: str) -> Film:
#         # TODO

#         return person
