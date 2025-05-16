from interfaces.analyzer import IContentAnalyzer
from interfaces.storage import IStorageHandler
from settings import Settings


class WOAExtractionUseCase:

    analyzer: IContentAnalyzer
    film_storage_handler: IStorageHandler
    person_storage_handler: IStorageHandler
    raw_content_storage_handler: IStorageHandler

    def __init__(
        self,
        raw_content_storage_handler: IStorageHandler,
        film_storage_handler: IStorageHandler,
        person_storage_handler: IStorageHandler,
        analyzer: IContentAnalyzer,
        settings: Settings = None,
    ):
        """_summary_

        Args:
            raw_content_storage_handler (IStorageHandler): the handler in charge of retrieving the raw Html content
            film_storage_handler (IStorageHandler): the handler in charge of storing the film entities
            person_storage_handler (IStorageHandler): the handler in charge of storing the person entities
            analyzer (IContentAnalyzer): the analyzer in charge of analyzing the content
            settings (Settings, optional): Defaults to None.
        """
        self.settings = settings or Settings()
        self.raw_content_storage_handler = raw_content_storage_handler
        self.film_storage_handler = film_storage_handler
        self.person_storage_handler = person_storage_handler
        self.analyzer = analyzer

    def execute(self, wait_for_completion: bool = False):
        """
        TODO:
        - [ ] parse the title, summary, and "tech spec" from the HTML content
        - [ ] split HTML content into chunks
        - [ ] vectorize chunks and store them in the vector database (Chroma)
        - [ ] ask questions to the vector database using LangChain and a LLM
        - [ ] store the results using the film and person storage handlers

        Args:
            wait_for_completion (bool, optional): _description_. Defaults to False.
        """
        i = 0
        for content in self.raw_content_storage_handler.scan():

            # parse the HTML content
            film = self.analyzer.analyze(content)

            if film is not None:
                # store the film entity
                self.film_storage_handler.insert(film)

            i += 1
            if i > 10:
                break
