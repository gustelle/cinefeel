import uvloop


async def main():

    from repositories.json_storage import JsonStorageHandler
    from settings import Settings
    from use_cases.index_films import MeiliIndexerUseCase
    from use_cases.scrape_wikipedia import WikipediaFilmScraperUseCase

    settings = Settings()
    storage_handler = JsonStorageHandler(settings=settings)

    scraping_use_case = WikipediaFilmScraperUseCase(
        settings=settings,
        storage_handler=storage_handler,
    )

    await scraping_use_case.execute()

    indexer = MeiliIndexerUseCase(
        settings=settings,
        persistence_handler=storage_handler,
    )

    indexer.execute(
        wait_for_completion=False,  # don't wait for the task to complete; return immediately
    )


if __name__ == "__main__":

    # run the main function
    uvloop.run(main())
