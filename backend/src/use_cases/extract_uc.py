from src.interfaces.analyzer import IContentAnalyzer
from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class JsonExtractionUseCase:
    """Use case for extracting information from Wikipedia pages."""

    html_extractor: IContentAnalyzer
    html_retrievers: list[IStorageHandler]
    storage_handlers: list[IStorageHandler]

    def __init__(
        self,
        storage_handlers: list[IStorageHandler],
        html_retrievers: list[IStorageHandler],
        html_extractor: IContentAnalyzer,
        settings: Settings = None,
    ):
        """_summary_

        Args:
            storage_handlers (list[IStorageHandler]): the handlers in charge of storing the entities
            html_retrievers (list[IStorageHandler]): the handlers in charge of storing the raw HTML content
            html_extractor (IContentAnalyzer): the analyzer in charge of analyzing the content
            settings (Settings, optional): Defaults to None.
        """
        self.settings = settings or Settings()
        self.storage_handlers = storage_handlers
        self.html_retrievers = html_retrievers
        self.html_extractor = html_extractor

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

        the_handler = None

        for retriever in self.html_retrievers:

            retriever_entity_type = retriever.entity_type

            for storage_handler in self.storage_handlers:
                if storage_handler.entity_type is retriever_entity_type:
                    the_handler = storage_handler
                    break

            if the_handler is None:
                raise ValueError(
                    f"Could not find a storage handler for the entity type: {retriever_entity_type}"
                )

            # scan the raw HTML content
            for content in retriever.scan():
                # parse the HTML content
                content = self.html_extractor.analyze(content)

                if content is not None:
                    # store the film entity
                    the_handler.insert(content.uid, content.model_dump(mode="json"))

                i += 1
                if i > 10:
                    break
