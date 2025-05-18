from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class HtmlExtractionUseCase:
    """Use case for extracting information from Wikipedia pages.

    TODO:
    - use dramatiq or dask worker to run the tasks in parallel
    """

    html_extractor: IContentAnalyzer
    html_retriever: IStorageHandler
    storage_handler: IStorageHandler

    def __init__(
        self,
        storage_handler: IStorageHandler,
        html_retriever: IStorageHandler,
        html_extractor: IContentAnalyzer,
        settings: Settings = None,
    ):
        """_summary_

        Args:
            storage_handler (IStorageHandler): _description_
            html_retriever (IStorageHandler): _description_
            html_extractor (IContentAnalyzer): _description_
            settings (Settings, optional): _description_. Defaults to None.
        """
        self.settings = settings or Settings()
        self.storage_handler = storage_handler
        self.html_retriever = html_retriever
        self.html_extractor = html_extractor

    def execute(self, wait_for_completion: bool = False):
        """

        Args:
            wait_for_completion (bool, optional): _description_. Defaults to False.
        """
        i = 0

        # scan the raw HTML content
        for content in self.html_retriever.scan():
            # parse the HTML content
            content = self.html_extractor.analyze(content)

            if content is not None:
                # store the film entity
                self.storage_handler.insert(
                    content.uid, content.model_dump(mode="json")
                )

            i += 1
            if i > 2:
                break
