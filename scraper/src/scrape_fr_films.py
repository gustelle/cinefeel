import asyncio
import time


async def main():

    start_time = time.time()

    # create a WikipediaRepository instance
    from repositories.meili_indexer import MeiliIndexer
    from repositories.scraper_repository import ConcurrentScraper
    from repositories.wikipedia_parser import WikipediaFilmSheetParser
    from repositories.wikipedia_repository import WikipediaRepository

    # create a scraper instance
    scraper = ConcurrentScraper(max_connections=4)
    parser = WikipediaFilmSheetParser()

    # create a WikipediaRepository instance
    wiki_repo = WikipediaRepository(scraper=scraper, parser=parser)

    indexer = MeiliIndexer(
        base_url="http://localhost:7700",
        api_key="cinefeel",
        index_name="films",
    )

    # get the films for each year
    async with wiki_repo:
        tasks = []
        for year in range(1906, 2024):

            tasks.append(
                wiki_repo.get_films(
                    page_list_id=f"Liste_de_films_français_sortis_en_{year}"
                )
            )

        # wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)

        print(f"Completed {len(results)} tasks")

        if any(isinstance(result, Exception) for result in results):
            print("Some tasks failed")
            for result in results:
                if isinstance(result, Exception):
                    print(f"Error: {result}")

        films = [film for result in results for film in result]

        if not films:
            print("No films found")
            return

        indexer.add_documents(
            docs=films,
            wait_for_completion=False,  # don't wait for the task to complete
        )

        print(f"Added {len(films)} films to the index")

    end_time = time.time()
    print(f"Execution time: {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    # run the script
    asyncio.run(main())
