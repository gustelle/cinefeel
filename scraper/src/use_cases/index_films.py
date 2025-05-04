from entities.film import Film
from repositories.meili_indexer import MeiliIndexer
from settings import Settings


class MeiliIndexerUseCase:

    indexer: MeiliIndexer

    def __init__(self, settings: Settings = None):
        self.settings = settings or Settings()
        self.indexer = MeiliIndexer(
            settings=self.settings,
        )

    async def execute(self, films: list[Film]) -> list[Film]:

        self.indexer.add_documents(
            docs=films,
            wait_for_completion=False,  # don't wait for the task to complete
        )

        print(f"Added {len(films)} films to the index")

        return films
