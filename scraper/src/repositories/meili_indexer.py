import meilisearch
import meilisearch.errors
import meilisearch.index
from entities.film import Film
from interfaces.indexer import IDocumentIndexer
from settings import Settings


class MeiliIndexer(IDocumentIndexer):

    client: meilisearch.Client
    index: meilisearch.index.Index

    def __init__(
        self,
        settings: Settings,
    ):

        self.client = meilisearch.Client(
            settings.meili_base_url, settings.meili_api_key
        )
        self.index = self.init_index(settings.meili_index_name)

    def init_index(self, index_name: str) -> meilisearch.index.Index:
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
                self.index.update_searchable_attributes(["title", "summary", "info"])
            else:
                print(f"Error getting index '{index_name}': {e}")

            print(f"Index '{index_name}' created: {e}")
        else:
            print(f"Index '{index_name}' already exists")

        return self.index

    def add_documents(
        self,
        docs: list[Film],
        wait_for_completion: bool = True,
    ):
        try:

            task_info = self.index.update_documents(
                [film.model_dump(mode="json") for film in docs], primary_key="uid"
            )

            if wait_for_completion:
                task_info = self.client.wait_for_task(task_info.task_uid)
                if task_info.status != "succeeded":
                    raise Exception(
                        f"Task failed: {task_info.status} - {task_info.error}"
                    )

        except Exception as e:
            print(f"Error adding documents to index '{self.index}': {e}")
