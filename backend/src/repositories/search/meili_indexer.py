from typing import Generator

import meilisearch
import meilisearch.errors
import meilisearch.index
from loguru import logger

from src.entities.movie import Movie
from src.entities.person import Person
from src.interfaces.storage import IStorageHandler
from src.settings import Settings


class MeiliHandler[T: Movie | Person](IStorageHandler[T]):

    client: meilisearch.Client
    index: meilisearch.index.Index
    settings: Settings
    entity_type: type[Movie | Person]

    def __init__(
        self,
        settings: Settings,
    ):

        self.client = meilisearch.Client(
            str(settings.search_base_url), settings.search_api_key
        )
        self.settings = settings

        if self.entity_type == Movie:
            self.index = self._init_index(self.settings.search_movies_index_name)
        elif self.entity_type == Person:
            self.index = self._init_index(self.settings.search_persons_index_name)
        else:
            raise ValueError(f"Unsupported entity type: {self.entity_type}")

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
            logger.trace(f"Index '{index_name}' not found. Attempting to create it.")
            if e.status_code == 404:
                t = self.client.create_index(
                    index_name,
                    options={"primaryKey": "uid"},
                )
                self.client.wait_for_task(t.task_uid)
                self.index = self.client.index(index_name)

                if self.entity_type == Movie:
                    self.index.update_searchable_attributes(
                        ["title", "summary.content", "actors.full_name"]
                    )
                elif self.entity_type == Person:
                    self.index.update_searchable_attributes(
                        ["biography.full_name", "biography.nicknames"]
                    )

            else:
                logger.error(f"Error getting index '{index_name}': {e}")
                raise

            logger.trace(f"Index '{index_name}' created: {e}")
        else:
            logger.trace(f"Index '{index_name}' already exists")

        return self.index

    def insert_many(
        self,
        contents: list[T],
    ):

        try:

            json_docs = []
            for doc in contents:
                try:
                    json_docs.append(doc.model_dump(mode="json"))
                except Exception as e:

                    logger.error(
                        f"Error serializing {doc.model_dump(mode='python')}: {e}"
                    )
                    continue

            if not json_docs:
                logger.warning("No valid documents to insert or update.")
                return

            self.index.update_documents(json_docs, primary_key="uid")

            logger.info(f"Indexation started with {len(json_docs)} documents.")

            # if wait_for_completion:
            #     task_info = self.client.wait_for_task(task_info.task_uid)
            #     if task_info.status != "succeeded":
            #         raise Exception(
            #             f"Task failed: {task_info.status} - {task_info.error}"
            #         )

        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            logger.error(f"Error adding documents to index '{self.index}': {e}")

    def insert(
        self,
        content: T,
    ) -> None:
        """inserts a single entity into the Meilisearch index.

        Args:
            content (T): The entity to be inserted.

        Returns:
            None
        """

        self.insert_many([content])

    def update(self, *args, **kwargs) -> None:
        raise NotImplementedError("Use insert or insert_many methods instead.")

    def select(self, content_id: str) -> T | None:
        raise NotImplementedError("Select method is not implemented yet.")

    def scan(self) -> Generator[tuple[str, T], None, None]:
        raise NotImplementedError("Scan method is not implemented yet.")

    def query(self, *args, **kwargs):
        raise NotImplementedError("Query method is not implemented yet.")
