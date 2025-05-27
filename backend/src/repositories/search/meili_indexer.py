import meilisearch
import meilisearch.errors
import meilisearch.index
from loguru import logger

from src.entities.film import Film
from src.entities.person import Person
from src.interfaces.indexer import IDocumentIndexer
from src.settings import Settings


class MeiliIndexer[T: Film | Person](IDocumentIndexer[T]):

    client: meilisearch.Client
    index: meilisearch.index.Index
    settings: Settings
    entity_type: type[Film | Person]

    def __init__(
        self,
        settings: Settings,
    ):

        self.client = meilisearch.Client(
            settings.meili_base_url, settings.meili_api_key
        )
        self.settings = settings

        if self.entity_type == Film:
            self.index = self._init_index(self.settings.meili_films_index_name)
        else:
            self.index = self._init_index(self.settings.meili_persons_index_name)

    def __class_getitem__(cls, generic_type):
        """Called when the class is indexed with a type parameter.
        Enables to guess the type of the entity being stored.

        Thanks to :
        https://stackoverflow.com/questions/57706180/generict-base-class-how-to-get-type-of-t-from-within-instance
        """
        new_cls = type(cls.__name__, cls.__bases__, dict(cls.__dict__))
        new_cls.entity_type = generic_type
        return new_cls

    def _init_index(self, index_name: str) -> meilisearch.index.Index:

        try:
            self.index = self.client.get_index(index_name)
        except meilisearch.errors.MeilisearchApiError as e:
            if e.status_code == 404:
                t = self.client.create_index(
                    index_name,
                    options={"primaryKey": "uid"},
                )
                self.client.wait_for_task(t.task_uid)
                self.index = self.client.index(index_name)

                if self.entity_type == Film:
                    self.index.update_searchable_attributes(
                        ["title", "summary", "info"]
                    )
                else:
                    # TODO
                    # self.index.update_searchable_attributes(
                    #     ["name", "summary", "info"]
                    # )
                    pass

            else:
                logger.info(f"Error getting index '{index_name}': {e}")

            logger.info(f"Index '{index_name}' created: {e}")
        else:
            logger.info(f"Index '{index_name}' already exists")

        return self.index

    def insert_or_update(
        self,
        docs: list[T],
        wait_for_completion: bool = True,
    ):

        try:

            json_docs = []
            for doc in docs:
                try:
                    logger.debug(f"Processing {type(doc).__name__}: '{doc.uid}'")
                    json_docs.append(doc.model_dump(mode="json"))
                except Exception as e:
                    import traceback

                    logger.error(traceback.format_exc())
                    logger.error(f"Error serializing document {doc.model_dump()}: {e}")
                    continue

            if not json_docs:
                logger.warning("No valid documents to insert or update.")
                return

            task_info = self.index.update_documents(json_docs, primary_key="uid")

            logger.info(
                f"Indexation started with {len(json_docs)} {type(doc).__name__}."
            )

            if wait_for_completion:
                task_info = self.client.wait_for_task(task_info.task_uid)
                if task_info.status != "succeeded":
                    raise Exception(
                        f"Task failed: {task_info.status} - {task_info.error}"
                    )

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            logger.error(f"Error adding documents to index '{self.index}': {e}")
