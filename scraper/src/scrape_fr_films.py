import time

import uvloop
from repositories.dask_runner import DaskRunner
from repositories.meili_indexer import MeiliIndexer
from repositories.scraper_repository import AsyncHttpClient
from repositories.wikipedia_parser import WikipediaFilmParser
from repositories.wikipedia_repository import WikipediaRepository
from settings import Settings


async def main():

    settings = Settings()

    scraper = AsyncHttpClient(settings=settings)
    parser = WikipediaFilmParser()
    indexer = MeiliIndexer(settings=settings)
    task_runner = DaskRunner()

    # init the wikipedia repository here to run in the main thread
    # and avoid the "RuntimeError: Event loop is closed" error
    wiki_repo = WikipediaRepository(
        http_client=scraper,
        parser=parser,
        settings=settings,
        task_runner=task_runner,
    )

    start_time = time.time()

    films = []

    # get the films for each year
    async with task_runner:
        async with wiki_repo:
            films = await wiki_repo.crawl()

            if not films:
                print("No films found")
                return

    if films is not None and len(films) > 0:
        indexer.add_documents(
            docs=films,
            wait_for_completion=False,  # don't wait for the task to complete
        )

        print(f"Added {len(films)} films to the index")

    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":

    # run the main function
    uvloop.run(main())
