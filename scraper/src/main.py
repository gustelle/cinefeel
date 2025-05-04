import uvloop


async def main():

    from settings import Settings
    from use_cases.index_films import MeiliIndexerUseCase
    from use_cases.scrape_wikipedia import WikipediaFilmScraperUseCase

    scraping_use_case = WikipediaFilmScraperUseCase(
        settings=Settings(),
    )

    films = await scraping_use_case.execute()

    indexer = MeiliIndexerUseCase(
        settings=Settings(),
    )

    films = indexer.execute(
        docs=films,
        wait_for_completion=False,  # don't wait for the task to complete
    )

    print(f"Added {len(films)} films to the index")


if __name__ == "__main__":

    # run the main function
    uvloop.run(main())
