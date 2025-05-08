from interfaces.analyzer import IContentAnalyzer
from interfaces.storage import IStorageHandler
from settings import Settings


class HtmlAnalysisUseCase:

    analyzer: IContentAnalyzer
    film_storage_handler: IStorageHandler
    person_storage_handler: IStorageHandler
    raw_content_storage_handler: IStorageHandler

    def __init__(
        self,
        raw_content_storage_handler: IStorageHandler,
        film_storage_handler: IStorageHandler,
        person_storage_handler: IStorageHandler,
        settings: Settings = None,
    ):
        """_summary_

        Args:
            raw_content_storage_handler (IStorageHandler): the handler in charge of retrieving the raw Html content
            film_storage_handler (IStorageHandler): the handler in charge of storing the film entities
            person_storage_handler (IStorageHandler): the handler in charge of storing the person entities
            settings (Settings, optional): Defaults to None.
        """
        self.settings = settings or Settings()
        self.raw_content_storage_handler = raw_content_storage_handler
        self.film_storage_handler = film_storage_handler
        self.person_storage_handler = person_storage_handler
        pass

    def execute(self, wait_for_completion: bool = False):
        # TODO
        pass
